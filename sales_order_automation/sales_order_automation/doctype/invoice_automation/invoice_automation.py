# Copyright (c) 2025, milind_jadhao and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


from urllib.parse import urlparse
import frappe, json, base64, openai
from urllib.parse import urlparse
from frappe.utils import getdate

import json

import re


# from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice

from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice








openai.api_key = frappe.get_doc("API Credentials").open_ai





class InvoiceAutomation(Document):
    pass











     


    



     
     

     
    




def get_file_content(file_url):
    """Fetch file content directly from File doctype"""
    file_doc = frappe.db.get("File", {"file_url": file_url})
    if not file_doc:
        frappe.throw(f"No file found for {file_url}")
    return frappe.get_doc("File", file_doc.name).get_content()


    

@frappe.whitelist()
def process_invoice_with_gpt5(doc):
    doc = json.loads(doc)
    read_invoice = doc.get("upload_invoice")

    # Get binary content directly from File doctype
    # Get binary content directly from File doctype
    file_content = get_file_content(read_invoice)

    # Base64 encode for GPT
    img_base64 = base64.b64encode(file_content).decode("utf-8")


    response = openai.chat.completions.create(
        model="gpt-4o-mini",   # ✅ lightweight vision+text model
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an invoice parser. Extract structured fields in clean JSON "
                    "with consistent field names matching ERPNext standards. "
                    "Keys: invoice_number, invoice_date, seller{name,address,tax_id,iban}, "
                    "client{name,address,tax_id}, items[{description,quantity,uom,rate,amount}], "
                    "summary{net_total,tax_percentage,tax_amount,grand_total}."
                )
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Parse this invoice image and return JSON only."
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}
                    }
                ]
            }
        ],
        response_format={"type": "json_object"}   # ✅ forces JSON output
    )


    # Parse GPT response safely
    # raw_content = response.choices[0].message["content"].strip()
    # data = json.loads(raw_content)

    raw_content = response.choices[0].message.content.strip()
    data = json.loads(raw_content)
    return data


def get_or_create_customer_with_address(client_data):
    customer_name = client_data["name"]

    if frappe.db.exists("Customer", customer_name):
        # Customer exists, just ensure address
        pass
    else:
        # Create customer
        customer = frappe.new_doc("Customer")
        customer.customer_name = customer_name
        customer.customer_type = "Company"
        customer.tax_id = client_data.get("tax_id")
        customer.customer_group = "All Customer Groups"
        customer.territory = "All Territories"
        customer.save(ignore_permissions=True)

    # ✅ Always create/ensure address here
    ensure_address_for_customer(customer_name, client_data.get("address"))

    if frappe.db.exists("Customer", customer_name):
        return customer_name
    
    return customer.name







def parse_us_address(address_str, default_country="United States"):
    """
    Parse a simple US-style address string into components.
    Expected format: <line1>, <city>, <state> <pincode>
    Example: "85942 Tucker Plains Apt. 982, Hernandezchester, SC 88596"
    """
    parts = [p.strip() for p in address_str.split(",")]

    # Basic structure
    address_line1 = parts[0] if len(parts) > 0 else ""
    city = parts[1] if len(parts) > 1 else ""
    state = ""
    pincode = ""

    if len(parts) > 2:
        # state and pincode are in the last part
        match = re.match(r"([A-Z]{2})\s+(\d+)", parts[2])
        if match:
            state, pincode = match.groups()

    return {
        "address_line1": address_line1,
        "city": city,
        "state": state,
        "pincode": pincode,
        "country": default_country
    }





def ensure_address_for_customer(customer_name, address_line):
    existing = frappe.get_all(
        "Dynamic Link",
        filters={"link_doctype": "Customer", "link_name": customer_name},
        fields=["parent"]
    )
    addr_data = parse_us_address(address_line)

    if not existing:
        addr = frappe.new_doc("Address")
        addr.address_title = customer_name
        addr.address_type = "Billing"
        addr.address_line1 = addr_data.get("address_line1") or "Not Provided"
        addr.city = addr_data.get("city") or ""
        addr.state = addr_data.get("state") or ""
        addr.pincode = addr_data.get("pincode") or ""
        addr.country = addr_data.get("country") or "India"
        addr.append("links", {
            "link_doctype": "Customer",
            "link_name": customer_name
        })
        addr.save(ignore_permissions=True)






    


def get_or_create_item(item_data):
    """Fetch or create an Item"""
    item_code = item_data["description"][:140]  # use description (truncate if long)
    if frappe.db.exists("Item", item_code):
        return item_code


    item = frappe.new_doc("Item")
    item.item_code = item_code
    item.item_name = item_data["description"]
    item.description = item_data["description"]
    item.stock_uom = "Nos"  # default to "Nos"
    item.item_group = "All Item Groups"  # adjust if you have specific groups
    item.is_sales_item = 1
    item.is_purchase_item = 0
    item.save(ignore_permissions=True)
    return item.item_code



@frappe.whitelist()
def create_sales_order(doc):

    doc = json.loads(doc)

    


    
    invoice_data = json.loads(doc["invoice_data"])

    # Ensure Customer exists
    customer_name = get_or_create_customer_with_address(invoice_data["client"])


    # Create Sales Order
    so = frappe.new_doc("Sales Order")
    so.naming_series = "SO-"   # adjust your naming series
    so.transaction_date = getdate(invoice_data["invoice_date"])
    so.delivery_date = getdate(invoice_data["invoice_date"])

    so.customer = customer_name

    # Add Items
    for item in invoice_data["items"]:
        item_code = get_or_create_item(item)

        qty = int(item.get("quantity", 0))   # or float if decimals possible
        rate = float(item.get("rate", 0))
        
        amount = item.get("amount")

        so.append("items", {
            "item_code": item_code,
            "delivery_date": doc.get("invoice_date"),
            "qty": qty,
            "uom": "Nos",
            "rate": rate,
            "amount": amount
        })


    so.save(ignore_permissions=True)
    so.submit()
    frappe.db.commit()


    invoice_name = create_sales_invoice_from_order(so.name)
    

    
    

    return so.name,invoice_name
    
    

    
    



@frappe.whitelist()
def create_sales_invoice_from_order(sales_order_name):
    # Create Sales Invoice from Sales Order
    si = make_sales_invoice(sales_order_name)
    si.save(ignore_permissions=True)
    si.submit()
    frappe.db.commit()
    return si.name