// Copyright (c) 2025, milind_jadhao and contributors
// For license information, please see license.txt

frappe.ui.form.on("Invoice Automation", {
	refresh: function(frm) {
		$('.sidebar-section').hide();
		$('.layout-side-section').remove();
		$(".form-footer").hide() 	
        // if (frm.doc.invoice_data) {
        //     try {
        //         let data = JSON.parse(frm.doc.invoice_data);

        //         let items_html = data.items.map(item => `
        //             <tr>
        //                 <td style="border:1px solid #ccc; padding:5px;">${item.description}</td>
        //                 <td style="border:1px solid #ccc; padding:5px; text-align:right;">${item.quantity}</td>
        //                 <td style="border:1px solid #ccc; padding:5px;">${item.unit_measure}</td>
        //                 <td style="border:1px solid #ccc; padding:5px; text-align:right;">${Number(item.net_price).toFixed(2)}</td>
        //                 <td style="border:1px solid #ccc; padding:5px; text-align:right;">${(item.net_price * item.quantity).toFixed(2)}</td>
        //                 <td style="border:1px solid #ccc; padding:5px; text-align:right;">${data.summary.vat_percentage}%</td>
        //                 <td style="border:1px solid #ccc; padding:5px; text-align:right;">${Number(item.gross_worth).toFixed(2)}</td>
        //             </tr>
        //         `).join("");

        //         let html = `
        //             <h3 style="text-align:center; margin-bottom:10px;">Invoice Preview</h3>

        //             <p><b>Invoice No:</b> ${data.invoice_number}</p>
        //             <p><b>Invoice Date:</b> ${data.invoice_date}</p>

        //             <h4>Seller</h4>
        //             <p>
        //                 ${data.seller.name}<br>
        //                 ${data.seller.address}<br>
        //                 Tax ID: ${data.seller.tax_id}<br>
        //                 IBAN: ${data.seller.iban}
        //             </p>

        //             <h4>Client</h4>
        //             <p>
        //                 ${data.client.name}<br>
        //                 ${data.client.address}<br>
        //                 Tax ID: ${data.client.tax_id}
        //             </p>

        //             <h4>Items</h4>
        //             <table style="border-collapse: collapse; width:100%; margin-top:10px;">
        //                 <thead>
        //                     <tr>
        //                         <th style="border:1px solid #ccc; padding:5px;">Description</th>
        //                         <th style="border:1px solid #ccc; padding:5px;">Qty</th>
        //                         <th style="border:1px solid #ccc; padding:5px;">Unit</th>
        //                         <th style="border:1px solid #ccc; padding:5px;">Net Price</th>
        //                         <th style="border:1px solid #ccc; padding:5px;">Net Worth</th>
        //                         <th style="border:1px solid #ccc; padding:5px;">VAT %</th>
        //                         <th style="border:1px solid #ccc; padding:5px;">Gross Worth</th>
        //                     </tr>
        //                 </thead>
        //                 <tbody>
        //                     ${items_html}
        //                 </tbody>
        //             </table>

        //             <h4 style="margin-top:15px;">Summary</h4>
        //             <p>
        //                 Net Worth: <b>${Number(data.summary.net_worth).toFixed(2)}</b><br>
        //                 VAT (${data.summary.vat_percentage}%): <b>${Number(data.summary.vat).toFixed(2)}</b><br>
        //                 Gross Worth: <b>${Number(data.summary.gross_worth).toFixed(2)}</b><br>
        //                 <b>Total: ${Number(data.summary.gross_worth).toFixed(2)}</b>
        //             </p>
        //         `;

        //         // render inside your HTML field
        //         frm.fields_dict["invoice_html"].$wrapper.html(html);

        //     } catch (e) {
        //         console.error("Invalid JSON in invoice_data:", e);
        //     }
        // }

	},
	process_invoice(frm){


		console.log("Processing invoice...");

		frappe.call({
			method: "sales_order_automation.sales_order_automation.doctype.invoice_automation.invoice_automation.process_invoice_with_gpt5",
			args: {
				doc:frm.doc
			},
			freeze: true,
			freeze_message: "Processing Invoices...",
			callback: function(r) {
				
				frm.set_value("invoice_data", JSON.stringify(r.message, null, 2));

				console.log(r.message);
				frappe.show_alert({message: __('Invoice processed successfully!'), indicator: 'green'});
			}
		});
		frm.refresh();

	},
	
	make_invoice(frm) {
		if (!frm.doc.invoice_data) {
			frappe.show_alert({message: __('Please process the invoice before creating it.'), indicator: 'red'});
			return;
		}

		
		frappe.call({
			method: "sales_order_automation.sales_order_automation.doctype.invoice_automation.invoice_automation.create_sales_order",
			args: {
				doc: frm.doc
			},
			freeze: true,
			freeze_message: "Creating Invoice...",
			callback: function(r) {
				if (r.message) {

					if (frm.doc.invoice_automation_child && frm.doc.invoice_automation_child.length > 0) {
						// ✅ Update existing rows
						frm.doc.invoice_automation_child.forEach(row => {
							frappe.model.set_value(row.doctype, row.name, "sales_invoice", r.message[1]);
							frappe.model.set_value(row.doctype, row.name, "sales_order", r.message[0]);
						});
					} else {
						// ✅ Add a new row if table is blank
						let child = frm.add_child("invoice_automation_child");
						frappe.model.set_value(child.doctype, child.name, "sales_invoice", r.message[1]);
						frappe.model.set_value(child.doctype, child.name, "sales_order", r.message[0]);
					}
					
					frm.refresh_field("invoice_automation_child");

					frm.save()
					
					// Success message
					frappe.show_alert({message: __('Invoice created successfully!'), indicator: 'green'});
					
					// Reload form
					// frm.reload_doc();
					
					
				}
			}
		});
	}



});
