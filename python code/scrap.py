import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import requests
from bs4 import BeautifulSoup
import pandas as pd
import threading
from concurrent.futures import ThreadPoolExecutor

# Proxy scraper tool class
class ProxyScraper:
    def __init__(self, root):
        self.root = root
        self.root.title("Proxy Management Tool")
        self.root.geometry("800x750")
        
        # Background color
        self.root.config(bg="#f5f5f5")
        
        # Define font
        self.font = ('Helvetica', 12)

        # Frame for the first three buttons in a horizontal line
        self.button_frame = tk.Frame(root, bg="#f5f5f5")
        self.button_frame.pack(pady=10)

        # GUI elements with improved styling
        self.url_label = tk.Label(root, text="Load Proxy Source URLs (TXT):", font=self.font, bg="#f5f5f5", fg="#333")
        self.url_label.pack(pady=5)

        self.load_file_button = tk.Button(self.button_frame, text="Load File", font=self.font, bg="#4CAF50", fg="white", relief="raised", command=self.load_urls)
        self.load_file_button.grid(row=0, column=0, padx=10)

        self.scrape_button = tk.Button(self.button_frame, text="Scrape Proxies", font=self.font, bg="#008CBA", fg="white", relief="raised", command=self.scrape_all_proxies)
        self.scrape_button.grid(row=0, column=1, padx=10)

        self.validate_button = tk.Button(self.button_frame, text="Validate Proxies", font=self.font, bg="#f39c12", fg="white", relief="raised", command=self.start_validate_proxies)
        self.validate_button.grid(row=0, column=2, padx=10)

        self.stop_button = tk.Button(self.button_frame, text="Stop Process", font=self.font, bg="#e74c3c", fg="white", relief="raised", command=self.stop_process, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=3, padx=10)

        self.result_text = scrolledtext.ScrolledText(root, width=80, height=20, font=self.font, bg="#f0f0f0", fg="#333", relief="flat")
        self.result_text.pack(pady=10)

        self.save_button = tk.Button(root, text="Save Working Proxies", font=self.font, bg="#e74c3c", fg="white", relief="raised", command=self.save_working_proxies)
        self.save_button.pack(pady=20, padx=10)

        # Copyright text at the bottom
        self.copyright_label = tk.Label(root, text="© 2024 Software by Muhsinalishah", font=('Helvetica', 10, 'italic'), bg="#f5f5f5", fg="#555")
        self.copyright_label.pack(side="bottom", pady=10)

        # Data storage
        self.urls = []
        self.proxies = []
        self.working_proxies = []

        # Progress display variables
        self.valid_count = 0
        self.invalid_count = 0

        # Labels to show live counts for valid and invalid proxies
        self.valid_label = tk.Label(root, text=f"Valid Proxies: {self.valid_count}", font=self.font, bg="#f5f5f5", fg="#333")
        self.valid_label.pack(pady=5)

        self.invalid_label = tk.Label(root, text=f"Invalid Proxies: {self.invalid_count}", font=self.font, bg="#f5f5f5", fg="#333")
        self.invalid_label.pack(pady=5)

        # Thread stop event
        self.stop_event = threading.Event()

    # Function to load URLs from a TXT file
    def load_urls(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if file_path:
            try:
                with open(file_path, "r") as file:
                    self.urls = [line.strip() for line in file if line.strip()]
                if self.urls:
                    messagebox.showinfo("Success", f"Loaded {len(self.urls)} URLs!")
                else:
                    messagebox.showerror("Error", "The file is empty or invalid.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {e}")

    # Function to scrape proxies from all loaded URLs with live updates
    def scrape_all_proxies(self):
        if not self.urls:
            messagebox.showerror("Error", "No URLs loaded. Please load a file with proxy source URLs.")
            return

        self.proxies = []  # Clear previous proxies
        self.result_text.delete(1.0, tk.END)  # Clear the text box

        for url in self.urls:
            try:
                response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
                soup = BeautifulSoup(response.text, "html.parser")

                # Extract proxy information (modify according to site structure)
                for row in soup.find_all("tr"):
                    columns = row.find_all("td")
                    if len(columns) >= 2:
                        ip = columns[0].text.strip()
                        port = columns[1].text.strip()
                        proxy = f"{ip}:{port}"

                        self.proxies.append(proxy)
                        # Insert the proxy into the display bar as it's scraped
                        self.result_text.insert(tk.END, f"Scraping: {proxy}\n")
                        self.result_text.yview(tk.END)  # Scroll to the bottom of the text box

                self.result_text.insert(tk.END, f"Finished scraping from: {url}\n")
            except Exception as e:
                self.result_text.insert(tk.END, f"Failed to scrape from {url}: {e}\n")

        # Display completion message
        if self.proxies:
            messagebox.showinfo("Success", f"Scraped {len(self.proxies)} proxies from all sources!")
        else:
            messagebox.showwarning("No Proxies", "No proxies found from the provided URLs.")

    # Function to validate proxies (runs in a separate thread)
    def start_validate_proxies(self):
        if not self.proxies:
            messagebox.showerror("Error", "No proxies to validate. Please scrape proxies first.")
            return

        # Reset counts before starting validation
        self.valid_count = 0
        self.invalid_count = 0
        self.result_text.delete(1.0, tk.END)  # Clear previous results

        # Update the labels for live counting
        self.valid_label.config(text=f"Valid Proxies: {self.valid_count}")
        self.invalid_label.config(text=f"Invalid Proxies: {self.invalid_count}")

        # Disable buttons to prevent multiple actions
        self.load_file_button.config(state=tk.DISABLED)
        self.scrape_button.config(state=tk.DISABLED)
        self.validate_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        # Start proxy validation in a new thread
        self.stop_event.clear()  # Reset stop event
        self.validation_thread = threading.Thread(target=self.validate_proxies)
        self.validation_thread.start()

    def validate_proxies(self):
        test_url = "https://www.google.com"  # The website to test proxy connectivity
        timeout = 5  # Timeout for proxy validation (seconds)

        self.result_text.insert(tk.END, "Validating proxies...\n")

        # Use ThreadPoolExecutor to validate multiple proxies concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(self.check_proxy, proxy, test_url, timeout): proxy for proxy in self.proxies}

            for future in futures:
                if self.stop_event.is_set():  # Check if stop event is triggered
                    self.result_text.insert(tk.END, "Process stopped by the user.\n")
                    break
                
                result = future.result()  # Wait for the result of the proxy validation
                if result:
                    self.valid_count += 1
                    self.result_text.insert(tk.END, f"Working: {result}\n")
                    self.valid_label.config(text=f"Valid Proxies: {self.valid_count}")  # Update live count
                else:
                    self.invalid_count += 1
                    self.result_text.insert(tk.END, f"Not Working: {futures[future]}\n")
                    self.invalid_label.config(text=f"Invalid Proxies: {self.invalid_count}")  # Update live count

                self.result_text.yview(tk.END)  # Scroll to the bottom of the text box

        # Re-enable buttons after validation
        self.load_file_button.config(state=tk.NORMAL)
        self.scrape_button.config(state=tk.NORMAL)
        self.validate_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

        # Display completion message with counts
        messagebox.showinfo("Validation Complete", f"{self.valid_count} working proxies found, {self.invalid_count} proxies are not working!")

    # Function to check a proxy by trying to access a website
    def check_proxy(self, proxy, test_url, timeout):
        try:
            proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
            response = requests.get(test_url, proxies=proxies, timeout=timeout)
            if response.status_code == 200:
                return proxy
            return None
        except Exception:
            return None

    # Function to save working proxies to a file
    def save_working_proxies(self):
        if not self.working_proxies:
            messagebox.showerror("Error", "No working proxies to save. Please validate proxies first.")
            return

        file_types = [("Text Files", "*.txt"), ("CSV Files", "*.csv")]
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=file_types)

        if file_path:
            try:
                if file_path.endswith(".txt"):
                    with open(file_path, "w") as f:
                        f.write("\n".join(self.working_proxies))
                elif file_path.endswith(".csv"):
                    df = pd.DataFrame({"Working Proxies": self.working_proxies})
                    df.to_csv(file_path, index=False)
                messagebox.showinfo("Success", f"Working proxies saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save proxies: {e}")

    # Function to stop the ongoing process
    def stop_process(self):
        self.stop_event.set()  # Signal the stop event to interrupt validation
        self.result_text.insert(tk.END, "Process has been stopped.\n")

# Main function to run the GUI application
def main():
    root = tk.Tk()
    app = ProxyScraper(root)
    root.mainloop()

if __name__ == "__main__":
    main()
