from robocorp.tasks import task
from robocorp import browser
from RPA.HTTP import HTTP
from RPA.Tables import Tables
from RPA.PDF import PDF
from RPA.Archive import Archive
from RPA.FileSystem import FileSystem
from RPA.Assistant import Assistant
from envvars.variables import *

page = browser.page()
pdf = PDF()

@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    open_robot_order_website(ROBOT_ORDER_WEBSITE_URL)
    #user_input_task()
    close_annoying_modal()
    orders = get_orders()
    fill_the_form(orders)

    for row in orders:
        pdf_file = f'output/receipt/{row["Order number"]}.pdf'
        screenshot = f'output/screenshots/{row["Order number"]}.png'
        embed_screenshot_to_receipt(pdf_file, screenshot)

    archive_receipts()
    clean_screenshots()

def user_input_task():
    """Takes website URL from user and passes it to open_robot_order_website()"""
    assistant = Assistant()
    assistant.add_heading("Input from user")
    assistant.add_text_input("text_input", placeholder="Please enter URL")
    assistant.add_submit_buttons("Submit", default="Submit")
    result = assistant.run_dialog()
    url = result.text_input
    open_robot_order_website(url)

def open_robot_order_website(url):
    """Opens the order website and clicks the OK button"""
    browser.configure(
        slowmo=100,
    )
    browser.goto(url)

def close_annoying_modal():
    """Closes the modal window"""
    page.get_by_role("button", name = "OK").click()

def get_orders():
    """Downloads orders.csv, overwrite is set True and loops it into table and returns it"""
    HTTP().download(url=ROBOT_ORDER_CSV_URL, overwrite=True)

    library = Tables()

    orders = library.read_table_from_csv(
        "orders.csv", columns=[
            "Order number",
            "Head",
            "Body",
            "Legs",
            "Address"
            ]
    )

    return orders

def fill_the_form(orders):
    """Fills the form from argument data, makes order and checks for alert-danger"""
    for row in orders:
        order_number = row["Order number"]
        page.get_by_label("1. Head:").select_option(str(row["Head"]))
        page.locator(f"input[type='radio'][value='{row['Body']}']").click()
        page.get_by_placeholder("Enter the part number for the legs").fill(str(row["Legs"]))
        page.get_by_placeholder("Shipping address").fill(str(row["Address"]))
        page.locator("button#preview").click()
        page.locator("button#order").click()
        alert_danger = page.locator('.alert-danger').is_visible()

        while(alert_danger):
            page.locator("button#order").click()
            alert_danger = page.locator('.alert-danger').is_visible()

        store_receipt_as_pdf(order_number)
        screenshot_robot(order_number)

        page.locator("button#order-another").click()

        close_annoying_modal()

def store_receipt_as_pdf(order_number):
    """ Makes a PDF of the receipt and stores the pdf to output/receipt/. Filenime is order number"""
    receipt_html = page.locator('.alert-success').inner_html()
    pdf.html_to_pdf(receipt_html, f"{RECEIPTS_PATH}{order_number}.pdf")

def screenshot_robot(order_number):
    """Takes a screenshot from the receipt and saves it"""
    page.screenshot(path=f"{SCREENSHOT_PATH}{order_number}.png")

def embed_screenshot_to_receipt(pdf_file, screenshot):
    """Embeds the screenshot to the receipt pdf"""
    list_of_files = [
        pdf_file,
        screenshot,
    ]
    pdf.add_files_to_pdf(
        files = list_of_files,
        target_document = pdf_file
    )

def archive_receipts():
    """Makes an receipts.zip from receipt folder """
    lib = Archive()
    lib.archive_folder_with_zip(RECEIPTS_PATH, 'receipts.zip', include='*.pdf')

def clean_screenshots():
    """Removes Screenshots"""
    file_system = FileSystem()
    if file_system.does_directory_exist(SCREENSHOT_PATH):
        file_system.empty_directory(SCREENSHOT_PATH)