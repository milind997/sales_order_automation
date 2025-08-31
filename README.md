# 🧾 Sales Order Automation

An AI-powered app for **automating Sales Order creation in Frappe/ERPNext**.  
Easily convert uploaded invoices into structured data and generate **Sales Orders** and **Sales Invoices** automatically.

---

## 🚀 Features

- Upload invoice files (PDF, JPG, PNG)
- AI-based document parsing and JSON conversion
- Automatic creation of **Sales Orders** in ERPNext
- Automatic creation of **Sales Invoices** linked to Sales Orders
- Error-free, fast, and integrated into ERPNext workflows

---

## ⚙️ Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench install-app sales_order_automation
