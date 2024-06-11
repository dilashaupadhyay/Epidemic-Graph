import tkinter as tk
from tkinter import filedialog, messagebox
import os
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

class VirusAnalysisApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Virus Analysis App")

        self.infection_rate_label = tk.Label(root, text="Enter Virus Infection Rate (1-10):")
        self.infection_rate_label.pack()
        self.infection_rate_entry = tk.Entry(root)
        self.infection_rate_entry.pack()

        self.load_folder_button = tk.Button(root, text="Load CSV Folder", command=self.load_csv_folder)
        self.load_folder_button.pack()

        self.load_geodata_button = tk.Button(root, text="Load District Geodata", command=self.load_district_geodata)
        self.load_geodata_button.pack()

        self.load_population_button = tk.Button(root, text="Load Population Data", command=self.load_population_data)
        self.load_population_button.pack()

        self.analyze_button = tk.Button(root, text="Analyze Data", command=self.analyze_data)
        self.analyze_button.pack()

        self.graph = nx.Graph()
        self.district_geodata = {}
        self.population_data = {}
        self.folder_selected = None

    def load_csv_folder(self):
        self.folder_selected = filedialog.askdirectory(title="Select Folder with CSV Files")
        if self.folder_selected:
            messagebox.showinfo("Success", f"Folder selected: {self.folder_selected}")
        else:
            messagebox.showinfo("Info", "No folder selected. Operation cancelled.")

    def load_district_geodata(self):
        file_path = filedialog.askopenfilename(title="Select District Geodata CSV File", filetypes=[("CSV Files", "*.csv")])
        if file_path:
            self.district_geodata = self.read_district_geodata(file_path)
            messagebox.showinfo("Success", "District geodata loaded successfully.")
        else:
            messagebox.showinfo("Info", "No file selected. Operation cancelled.")

    def load_population_data(self):
        file_path = filedialog.askopenfilename(title="Select Population Data CSV File", filetypes=[("CSV Files", "*.csv")])
        if file_path:
            self.population_data = self.read_population_data(file_path)
            messagebox.showinfo("Success", "Population data loaded successfully.")
        else:
            messagebox.showinfo("Info", "No file selected. Operation cancelled.")

    def analyze_data(self):
        try:
            infection_rate = float(self.infection_rate_entry.get())
            if not self.folder_selected:
                raise Exception("No folder selected.")
            if not self.district_geodata:
                raise Exception("District geodata not loaded.")
            if not self.population_data:
                raise Exception("Population data not loaded.")

            for filename in os.listdir(self.folder_selected):
                if filename.endswith(".csv"):
                    filepath = os.path.join(self.folder_selected, filename)
                    self.read_and_analyze_csv(filepath, infection_rate, self.population_data, self.district_geodata)
            
            self.visualize_graph()

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def read_and_analyze_csv(self, filepath, infection_rate, population_data, district_geodata):
        df = pd.read_csv(filepath)
        from_district = os.path.splitext(os.path.basename(filepath))[0].split("_")[0]
        for _, row in df.iterrows():
            to_district = row['To District']
            incoming_traffic = row['Incoming Traffic']
            outgoing_traffic = row['Outgoing Traffic']
            if from_district in district_geodata and to_district in district_geodata:
                from_population = population_data[from_district]['Population']
                to_population = population_data[to_district]['Population']
                avg_population = (from_population + to_population) / 2
                if from_district in population_data and 'Area' in population_data[from_district]:
                    population_density = from_population / population_data[from_district]['Area']   # Population/Area
                else:
                    population_density = 1  # Default value if 'Area' is not available
                weight = (population_density * (incoming_traffic + outgoing_traffic) * (infection_rate / 10)) / avg_population  # Adjusted weight
                self.graph.add_edge(from_district, to_district, weight=weight)

    def visualize_graph(self):
        plt.figure(figsize=(10, 8))
        pos = {district: (longitude, latitude) for district, (latitude, longitude) in self.district_geodata.items()}

        weights = [self.graph[u][v]['weight'] for u, v in self.graph.edges()]

        # Set colors for nodes based on infection rate
        node_colors = []
        for node in self.graph.nodes():
            infection_rate = sum([self.graph[u][v]['weight'] for u, v in self.graph.edges(node)])  # Sum of weights for connected edges
            if infection_rate < 1:  # Safest nodes (green)
                color = 'green'
            elif infection_rate >= 3:  # Most infected nodes (red)
                color = 'red'
            else:  # Default sky blue
                color = 'skyblue'
            node_colors.append(color)

        nx.draw(self.graph, pos, with_labels=True, node_color=node_colors, node_size=180, edge_color='black', font_size=8, font_color='black', font_weight='bold' )

        # Adjust edge labels to fit
        edge_labels = {(u, v): round(self.graph[u][v]['weight'], 2) for u, v in self.graph.edges()}
        nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=edge_labels, font_color='blue', font_size=8, font_weight='bold')

        plt.title("District Connection Graph Based on Virus Infection Rate and Traffic")
        plt.xlabel("Longitude")
        plt.ylabel("Latitude")
        plt.grid(False)
        plt.show()

    def read_district_geodata(self, file_path):
        df = pd.read_csv(file_path)
        district_geodata = {}
        for _, row in df.iterrows():
            district = row['District']
            latitude = row['Latitude']
            longitude = row['Longitude']
            district_geodata[district] = (latitude, longitude)
        return district_geodata

    def read_population_data(self, file_path):
        df = pd.read_csv(file_path)
        population_data = {}
        for _, row in df.iterrows():
            district = row['District']
            population = row['Population']
            area = row['Area']  # Assuming the Area column is present in the population data file
            population_data[district] = {'Population': population, 'Area': area}
        return population_data

if __name__ == "__main__":
    root = tk.Tk()
    app = VirusAnalysisApp(root)
    root.mainloop()
