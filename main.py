import customtkinter as ctk
from datetime import date, datetime, timedelta
from tkcalendar import Calendar
from tkinter import filedialog
from openpyxl import Workbook
from database.db import (
    initialize_database,
    add_medicine,
    update_medicine,
    delete_medicine,
    fetch_medicines,
    dashboard_counts,
    fetch_categories,
    add_category,
)
from ui.theme import THEMES, apply_appearance, set_theme
from ui.settings import load_settings, save_settings
ctk.set_default_color_theme("blue")
initialize_database()


class PharmacyApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Pharmacy Management System")
        self.geometry("1200x720")
        self.minsize(1000, 650)
        saved = load_settings()
        self.theme_name = saved["theme_name"]
        self.theme = set_theme(self.theme_name)
        apply_appearance(saved["mode"])
        self.current_mode = saved["mode"]
        self.low_stock_threshold = saved["low_stock_threshold"]
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.build_sidebar()
        self.build_content()

        self.show_dashboard()

    # ---------- Sidebar ----------
    def build_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self,
            width=220,
            fg_color=self.theme["sidebar"],
            corner_radius=0,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        title = ctk.CTkLabel(
            self.sidebar,
            text="💊 Pharmacy",
            text_color="white",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        title.pack(pady=(35, 30))

        self.nav_buttons = []
        items = [
            ("Dashboard", self.show_dashboard),
            ("Medicines", self.show_medicines),
            ("Calendar", self.show_calendar),
            ("Settings", self.show_settings),
        ]

        for text, command in items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=text,
                command=command,
                height=42,
                corner_radius=10,
                fg_color="transparent",
                hover_color=self.theme["hover"],
                anchor="w",
            )
            btn.pack(fill="x", padx=18, pady=6)
            self.nav_buttons.append(btn)

        ctk.CTkLabel(
            self.sidebar,
            text="Usability-focused\nPharmacy System",
            text_color=("#CBD5E1", "#94A3B8"),
            justify="left",
        ).pack(side="bottom", padx=20, pady=25, anchor="w")

    # ---------- Main content ----------
    def build_content(self):
        self.content = ctk.CTkFrame(self, fg_color=("#F8FAFC", "#0F172A"), corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_rowconfigure(1, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.header = ctk.CTkFrame(self.content, fg_color="transparent")
        self.header.grid(row=0, column=0, sticky="ew", padx=30, pady=(25, 10))
        self.header.grid_columnconfigure(0, weight=1)

        self.page_title = ctk.CTkLabel(
            self.header,
            text="Dashboard",
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color=self.theme["text"],
        )
        self.page_title.grid(row=0, column=0, sticky="w")

        self.date_label = ctk.CTkLabel(
            self.header,
            text=date.today().strftime("%d %B %Y"),
            text_color=self.theme["muted"],
        )
        self.date_label.grid(row=1, column=0, sticky="w")

        self.page = ctk.CTkScrollableFrame(
            self.content,
            fg_color="transparent",
        )
        self.page.grid(row=1, column=0, sticky="nsew", padx=30, pady=10)

    def clear_page(self):
        for widget in self.page.winfo_children():
            widget.destroy()
    def refresh_current_page(self):
     text = self.page_title.cget("text")
     {
        "Dashboard": self.show_dashboard,
        "Medicine Management": self.show_medicines,
        "Calendar": self.show_calendar,
        "Settings": self.show_settings,
     }.get(text, self.show_dashboard)()

    def card(self, parent, title, value, command=None):
        frame = ctk.CTkFrame(parent, corner_radius=16, fg_color=self.theme["card"])
        frame.pack(side="left", fill="both", expand=True, padx=8, pady=8)

        title_label = ctk.CTkLabel(
            frame,
            text=title,
            text_color=self.theme["muted"],
            font=ctk.CTkFont(size=14),
        )
        title_label.pack(anchor="w", padx=20, pady=(18, 5))

        value_label = ctk.CTkLabel(
            frame,
            text=str(value),
            text_color=self.theme["text"],
            font=ctk.CTkFont(size=30, weight="bold"),
        )
        value_label.pack(anchor="w", padx=20, pady=(0, 18))
        if command:
           for widget in (frame, title_label, value_label):
             widget.configure(cursor="hand2")
             widget.bind("<Button-1>", lambda event: command())
        return frame

    # ---------- Dashboard ----------
    def show_dashboard(self):
        self.page_title.configure(text="Dashboard")
        self.clear_page()

        total, stock, low, expired = dashboard_counts(self.low_stock_threshold)
        all_meds = fetch_medicines()
        last_updated_times = [m[6] for m in all_meds if m[6]]
        most_recent = max(last_updated_times) if last_updated_times else "No updates yet"
        today = date.today()
        expiring_soon = 0
        for med in fetch_medicines():
           try:
             expiry_date = datetime.strptime(med[5], "%Y-%m-%d").date()
             if today <= expiry_date <= today + timedelta(days=30):
                expiring_soon += 1
           except (ValueError, TypeError):
                continue
        cards = ctk.CTkFrame(self.page, fg_color="transparent")
        cards.pack(fill="x", pady=(5, 20))

        self.card(cards, "Medicine Types", total, command=self.show_medicines)
        self.card(cards, "Total Stock", stock, command=self.show_medicines)
        self.card(cards,"Low Stock Items", low, command=lambda: self.go_to_medicines_with_filter(stock_filter="Low Stock"),)
        self.card(cards, "Expired Items", expired, command=lambda: self.go_to_medicines_with_filter(stock_filter="Expired"),)
        self.card(cards, "Expiring Soon (30d)", expiring_soon, command=self.show_calendar)
        ctk.CTkLabel(
            self.page,
            text=f"Last medicine record update: {most_recent}",
            text_color=self.theme["muted"],
            font=ctk.CTkFont(size=12),
        ).pack(anchor="w", padx=8, pady=(0, 10))
        welcome = ctk.CTkFrame(self.page, corner_radius=18, fg_color=self.theme["card"])
        welcome.pack(fill="x", padx=8, pady=8)

        ctk.CTkLabel(
            welcome,
            text="Welcome to your Pharmacy Management System",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=self.theme["text"],
        ).pack(anchor="w", padx=25, pady=(25, 8))

        ctk.CTkLabel(
            welcome,
            text=(
                "The dashboard gives you a quick overview of medicines, "
                "stock levels and expiry risks.\n"
                "Use the sidebar to manage medicines, search/filter records, "
                "check the calendar and customize the interface."
            ),
            justify="left",
            text_color=self.theme["muted"],
        ).pack(anchor="w", padx=25, pady=(0, 25))

        quick = ctk.CTkFrame(self.page, fg_color="transparent")
        quick.pack(fill="x", padx=8, pady=10)

        ctk.CTkButton(
            quick,
            text="➕ Add Medicine",
            command=self.open_medicine_form,
            fg_color=self.theme["primary"],
            hover_color=self.theme["hover"],
            height=44,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            quick,
            text="🔎 Search Medicines",
            command=self.show_medicines,
            fg_color=self.theme["primary"],
            hover_color=self.theme["hover"],
            height=44,
        ).pack(side="left")

    # ---------- Medicines ----------
    def show_medicines(self):
        self.page_title.configure(text="Medicine Management")
        self.clear_page()

        top = ctk.CTkFrame(self.page, fg_color="transparent")
        top.pack(fill="x", pady=(5, 10))

        search = ctk.CTkEntry(top, placeholder_text="Search medicine name...")
        search.pack(side="left", fill="x", expand=True, padx=(8, 8))
        search.bind(
           "<KeyRelease>",
            lambda e: self.refresh_medicine_table(search.get(), category.get(), stock_filter.get()),
        )

        category = ctk.CTkComboBox(
            top,
            values=["All"] + fetch_categories(),
            width=150,
        )
        category.set("All")
        category.pack(side="left", padx=8)

        stock_filter = ctk.CTkComboBox(
            top,
            values=["All Stock", "Low Stock", "Expired"],
            width=130,
        )
        stock_filter.set("All Stock")
        stock_filter.pack(side="left", padx=8)
        def live_filter(event=None):
           self.refresh_medicine_table(search.get(), category.get(), stock_filter.get())

        search.bind("<KeyRelease>", live_filter)
        category.configure(command=lambda choice: live_filter())
        stock_filter.configure(command=lambda choice: live_filter())
        ctk.CTkButton(
            top,
            text="Search / Filter",
            command=lambda: self.refresh_medicine_table(
                search.get(), category.get(), stock_filter.get()
            ),
            fg_color=self.theme["primary"],
            hover_color=self.theme["hover"],
        ).pack(side="left", padx=(8, 0))

        ctk.CTkButton(
            top,
            text="+ Add",
            command=self.open_medicine_form,
            width=90,
        ).pack(side="left", padx=(8, 0))

        ctk.CTkButton(
            top,
            text="⬇ Export Excel",
            command=self.export_medicines_excel,
            width=130,
        ).pack(side="left", padx=(8, 0))

        table = ctk.CTkFrame(self.page, corner_radius=16, fg_color=self.theme["card"])
        table.pack(fill="both", expand=True, padx=8, pady=8)

        self.table_container = table
        self.refresh_medicine_table()

    def go_to_medicines_with_filter(self, stock_filter="All Stock"):
     self.show_medicines()
     self.refresh_medicine_table(stock_filter=stock_filter)

    def refresh_medicine_table(self, search_text="", category="All", stock_filter="All Stock"):
        for widget in self.table_container.winfo_children():
            widget.destroy()

        headers = ["ID", "Name", "Category", "Quantity", "Price", "Expiry", "Last Updated", "Actions"]
        widths = [55, 180, 110, 80, 80, 140, 150]

        for i, header in enumerate(headers):
            ctk.CTkLabel(
                self.table_container,
                text=header,
                font=ctk.CTkFont(weight="bold"),
                text_color=self.theme["muted"],
            ).grid(row=0, column=i, padx=8, pady=12, sticky="w")

        medicines = fetch_medicines()
        def expiry_sort_key(med):
            try:
              return datetime.strptime(med[5], "%Y-%m-%d").date()
            except (ValueError, TypeError):
              return date.max
        medicines = sorted(medicines, key=expiry_sort_key)
        row_index = 1
        for med in medicines:
            med_id, name, category_name, quantity, price, expiry, last_updated = med

            if search_text and search_text.lower() not in name.lower():
                continue
            if category != "All" and category_name != category:
                continue
            if stock_filter == "Low Stock" and quantity > self.low_stock_threshold:
                continue
            if stock_filter == "Expired":
               try:
                  expiry_date = datetime.strptime(expiry, "%Y-%m-%d").date()
                  if expiry_date >= date.today():
                     continue
               except (ValueError, TypeError):
                     continue
            values = [
                med_id,
                name,
                category_name,
                quantity,
                f"₹{price:.2f}",
                expiry,
                last_updated or "—",
            ]

            for col, value in enumerate(values):
                ctk.CTkLabel(
                    self.table_container,
                    text=str(value),
                    text_color=self.theme["text"],
                ).grid(row=row_index, column=col, padx=8, pady=9, sticky="w")

            action_box = ctk.CTkFrame(self.table_container, fg_color="transparent")
            action_box.grid(row=row_index, column=7, padx=5, sticky="w")

            ctk.CTkButton(
                action_box,
                text="Edit",
                width=60,
                command=lambda m=med: self.open_medicine_form(m),
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                action_box,
                text="Delete",
                width=60,
                fg_color="#DC2626",
                hover_color="#B91C1C",
                command=lambda mid=med_id: self.delete_medicine_confirm(mid),
            ).pack(side="left", padx=2)

            row_index += 1

        if row_index == 1:
            ctk.CTkLabel(
                self.table_container,
                text="No medicines found.",
                text_color=self.theme["muted"],
            ).grid(row=1, column=0, columnspan=8, pady=40)
    def export_medicines_excel(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            title="Save Medicine Inventory As",
            initialfile="medicine_inventory.xlsx",
        )
        if not file_path:
            return 

        medicines = fetch_medicines()
        try:
            wb = Workbook()
            ws = wb.active
            ws.title = "Medicines"

            headers = ["ID", "Name", "Category", "Quantity", "Price", "Expiry Date", "Last Updated"]
            ws.append(headers)

            for med in medicines:
                ws.append(list(med))

            for col in ws.columns:
                max_length = max(len(str(cell.value)) if cell.value else 0 for cell in col)
                ws.column_dimensions[col[0].column_letter].width = max_length + 2
        
            wb.save(file_path)
            self.show_error_dialog("Export Complete", f"Inventory exported to:\n{file_path}")
        
        except OSError as exc:
            self.show_error_dialog("Export Failed", str(exc))

    def open_medicine_form(self, medicine=None):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Medicine" if medicine else "Add Medicine")
        dialog.geometry("450x520")
        dialog.transient(self)
        dialog.grab_set()

        fields = {}
        error_labels = {}
        labels = [
            ("Name", "name"),
            ("Category", "category"),
            ("Quantity", "quantity"),
            ("Price", "price"),
            ("Expiry Date (YYYY-MM-DD)", "expiry"),
        ]

        for i, (label_text, key) in enumerate(labels):
            ctk.CTkLabel(dialog, text=label_text).pack(anchor="w", padx=30, pady=(15, 5))
            if key == "category":
               entry = ctk.CTkComboBox(dialog, values=fetch_categories())
               entry.set("")
            else:
               entry = ctk.CTkEntry(dialog)
            entry.pack(fill="x", padx=30)
            fields[key] = entry
            error_label = ctk.CTkLabel(
               dialog,
               text="",
               text_color="#DC2626",
               font=ctk.CTkFont(size=12),
               anchor="w",
            )
            error_label.pack(fill="x", padx=30, pady=(2, 0))
            error_labels[key] = error_label
        def clear_errors():
           for key, entry in fields.items():
             entry.configure(border_color=("#979DA2", "#565B5E"))  # default CTk border
             error_labels[key].configure(text="")
        if medicine:
            _, name, category, quantity, price, expiry, _ = medicine
            fields["name"].insert(0, name)
            fields["category"].insert(0, category)
            fields["quantity"].insert(0, str(quantity))
            fields["price"].insert(0, str(price))
            fields["expiry"].insert(0, expiry)

        def save():
                clear_errors()
                has_error = False
                name = fields["name"].get().strip()
                category = fields["category"].get().strip() or "Other"
                add_category(category)
                expiry = fields["expiry"].get().strip()
                if not name:
                  error_labels["name"].configure(text="Name is required")
                  fields["name"].configure(border_color="#DC2626")
                  has_error = True
                try:
                   quantity = int(fields["quantity"].get())
                   if quantity < 0:
                      raise ValueError
                except ValueError:
                  error_labels["quantity"].configure(text="Enter a valid non-negative number")
                  fields["quantity"].configure(border_color="#DC2626")
                  has_error = True
                  quantity = None
                try:
                   price = float(fields["price"].get())
                   if price < 0:
                      raise ValueError
                except ValueError:
                   error_labels["price"].configure(text="Enter a valid non-negative price")
                   fields["price"].configure(border_color="#DC2626")
                   has_error = True
                   price = None
                

                if not expiry:
                    error_labels["expiry"].configure(text="Expiry date is required")
                    fields["expiry"].configure(border_color="#DC2626")
                    has_error = True
                else:
                    try:
                       datetime.strptime(expiry, "%Y-%m-%d")
                    except ValueError:
                       error_labels["expiry"].configure(text="Use format YYYY-MM-DD")
                       fields["expiry"].configure(border_color="#DC2626")
                       has_error = True
                if has_error:
                    return
                if medicine:
                    update_medicine(
                        medicine[0], name, category, quantity, price, expiry
                    )
                else:
                    add_medicine(name, category, quantity, price, expiry)

                dialog.destroy()
                self.show_medicines()
                

        ctk.CTkButton(
            dialog,
            text="Save Medicine",
            command=save,
            fg_color=self.theme["primary"],
            hover_color=self.theme["hover"],
            height=44,
        ).pack(fill="x", padx=30, pady=25)
        dialog.bind("<Return>", lambda event: save())    
    def delete_medicine_confirm(self, medicine_id):
        self.show_confirm_dialog(
            "Delete Medicine",
            "Are you sure you want to delete this medicine?",
            on_confirm=lambda: (delete_medicine(medicine_id), self.show_medicines()),
        )

    def show_confirm_dialog(self, title, message, on_confirm):
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("380x180")
        dialog.transient(self)
        dialog.grab_set()
        dialog.configure(fg_color=self.theme["card"])

        ctk.CTkLabel(
            dialog,
            text=message,
            text_color=self.theme["text"],
            wraplength=320,
            justify="center",
        ).pack(padx=25, pady=(30, 20))

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack(pady=10)

        def confirm_and_close():
            dialog.destroy()
            on_confirm()

        ctk.CTkButton(
            btn_row,
            text="Cancel",
            fg_color="transparent",
            border_width=1,
            text_color=self.theme["text"],
            command=dialog.destroy,
            width=100,
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_row,
            text="Confirm",
            fg_color="#DC2626",
            hover_color="#B91C1C",
            command=confirm_and_close,
            width=100,
        ).pack(side="left", padx=10)

    def show_error_dialog(self, title, message):
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("380x160")
        dialog.transient(self)
        dialog.grab_set()
        dialog.configure(fg_color=self.theme["card"])

        ctk.CTkLabel(
            dialog,
            text=message,
            text_color=self.theme["text"],
            wraplength=320,
            justify="center",
        ).pack(padx=25, pady=(30, 20))

        ctk.CTkButton(
            dialog,
            text="OK",
            fg_color=self.theme["primary"],
            hover_color=self.theme["hover"],
            command=dialog.destroy,
            width=100,
        ).pack(pady=10)
    # ---------- Calendar ----------
    def show_calendar(self):
        self.page_title.configure(text="Calendar")
        self.clear_page()

        wrapper = ctk.CTkFrame(self.page, corner_radius=16, fg_color=self.theme["card"])
        wrapper.pack(fill="both", expand=True, padx=8, pady=8)

        ctk.CTkLabel(
            wrapper,
            text="Medicine Expiry Calendar",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.theme["text"],
        ).pack(pady=(20, 10))

        cal = Calendar(wrapper, selectmode="day", date_pattern="yyyy-mm-dd")
        cal.pack(pady=20)

        result = ctk.CTkLabel(wrapper, text="", text_color=self.theme["muted"])
        result.pack(pady=10)

        def show_selected():
            selected = cal.get_date()
            matched = [
                med for med in fetch_medicines() if med[5] == selected
            ]
            if matched:
                names = ", ".join(med[1] for med in matched)
                result.configure(text=f"Expiry on {selected}: {names}")
            else:
                result.configure(text=f"No expiry recorded for {selected}.")

        ctk.CTkButton(
            wrapper,
            text="Check Selected Date",
            command=show_selected,
        ).pack(pady=10)

    # ---------- Settings ----------
    def show_settings(self):
        self.page_title.configure(text="Settings")
        self.clear_page()

        card = ctk.CTkFrame(self.page, corner_radius=16, fg_color=self.theme["card"])
        card.pack(fill="x", padx=8, pady=8)

        ctk.CTkLabel(
            card,
            text="Appearance",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.theme["text"],
        ).pack(anchor="w", padx=25, pady=(25, 15))

        ctk.CTkLabel(card, text="Mode").pack(anchor="w", padx=25)
        mode = ctk.CTkComboBox(
            card,
            values=["Light", "Dark", "System"],
            command=self.change_mode,
            width=200,
        )
        mode.set(self.current_mode)
        mode.pack(anchor="w", padx=25, pady=(5, 20))

        ctk.CTkLabel(card, text="Custom Theme").pack(anchor="w", padx=25)
        theme = ctk.CTkComboBox(
            card,
            values=list(THEMES.keys()),
            command=self.change_theme,
            width=200,
        )
        theme.set(self.theme_name)
        theme.pack(anchor="w", padx=25, pady=(5, 25))
        ctk.CTkLabel(card, text="Low Stock Threshold").pack(anchor="w", padx=25)
        threshold_entry = ctk.CTkEntry(card, width=200)
        threshold_entry.insert(0, str(self.low_stock_threshold))
        threshold_entry.pack(anchor="w", padx=25, pady=(5, 10))

        def save_threshold():
           try:
              value = int(threshold_entry.get())
              if value < 0:
                 raise ValueError
              self.low_stock_threshold = value
              save_settings(self.theme_name, self.current_mode, value)
              self.show_error_dialog("Saved", f"Low stock threshold set to {value}.")
           except ValueError:
              self.show_error_dialog("Invalid Input", "Enter a non-negative whole number.")
        ctk.CTkButton(
           card,
           text="Save Threshold",
           command=save_threshold,
           fg_color=self.theme["primary"],
           hover_color=self.theme["hover"],
            width=200,
        ).pack(anchor="w", padx=25, pady=(0, 25))
    def change_mode(self, mode):
        apply_appearance(mode)
        self.current_mode = mode
        save_settings(self.theme_name, self.current_mode)
        self.refresh_current_page()
    def change_theme(self, name):
        self.theme_name = name
        self.theme = set_theme(name)
        save_settings(self.theme_name, self.current_mode)
        # Sidebar colors
        self.sidebar.configure(fg_color=self.theme["sidebar"])
        self.refresh_current_page()
        self.update_theme_widgets()

    def update_theme_widgets(self):
        self.page_title.configure(text_color=self.theme["text"])

    def run(self):
        self.mainloop()


if __name__ == "__main__":
    app = PharmacyApp()
    app.run()