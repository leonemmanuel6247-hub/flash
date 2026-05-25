import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import queue
from utils import get_local_ip
from server import FileServer
from client import FileClient


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('Flash')
        self.root.resizable(False, False)
        self.server = None
        self.queue = queue.Queue()
        self.selected_file = None
        self._build_ui()
        self._check_queue()

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        tk.Label(main, text='Flash', font=('Helvetica', 16, 'bold')).grid(
            row=0, column=0, columnspan=2, pady=10)

        # Panneau ENVOYER
        envoi = ttk.LabelFrame(main, text='ENVOYER', padding=10)
        envoi.grid(row=1, column=0, pady=10, padx=10, sticky='n')

        tk.Label(envoi, text='IP cible:').grid(row=0, column=0, sticky='e')
        self.entry_ip = tk.Entry(envoi, width=18)
        self.entry_ip.grid(row=0, column=1, padx=5)

        tk.Label(envoi, text='Port:').grid(row=1, column=0, sticky='e')
        self.entry_port = tk.Entry(envoi, width=18)
        self.entry_port.insert(0, '5001')
        self.entry_port.grid(row=1, column=1, padx=5)

        self.lbl_file = tk.Label(envoi, text='Aucun fichier', fg='gray')
        self.lbl_file.grid(row=2, column=0, columnspan=2, pady=5)

        btn_choisir = tk.Button(envoi, text='Choisir fichier', command=self._choose_file)
        btn_choisir.grid(row=3, column=0, pady=5, sticky='e')
        btn_dossier = tk.Button(envoi, text='Choisir dossier', command=self._choose_directory)
        btn_dossier.grid(row=3, column=1, pady=5, sticky='w')
        
        btn_envoyer = tk.Button(envoi, text='Envoyer', command=self._send_file)
        btn_envoyer.grid(row=4, column=0, columnspan=2, pady=5)

        self.bar_envoi = ttk.Progressbar(envoi, length=280, mode='determinate')
        self.bar_envoi.grid(row=5, column=0, columnspan=2, pady=10)

        # Panneau RECEVOIR
        recu = ttk.LabelFrame(main, text='RECEVOIR', padding=10)
        recu.grid(row=1, column=1, pady=10, padx=10, sticky='n')

        tk.Label(recu, text=f'Mon IP: {get_local_ip()}').grid(row=0, column=0, columnspan=2, sticky='w')

        tk.Label(recu, text='Port:').grid(row=1, column=0, sticky='e')
        self.entry_port_recu = tk.Entry(recu, width=18)
        self.entry_port_recu.insert(0, '5001')
        self.entry_port_recu.grid(row=1, column=1, padx=5)

        self.btn_serveur = tk.Button(recu, text='Demarrer serveur', command=self._toggle_server)
        self.btn_serveur.grid(row=2, column=0, columnspan=2, pady=10)

        self.lbl_status = tk.Label(recu, text='Serveur inactif', fg='red')
        self.lbl_status.grid(row=3, column=0, columnspan=2)

        self.bar_recu = ttk.Progressbar(recu, length=280, mode='determinate')
        self.bar_recu.grid(row=4, column=0, columnspan=2, pady=10)

        self.lst_recu = tk.Listbox(recu, height=6)
        self.lst_recu.grid(row=5, column=0, columnspan=2, pady=10, sticky='we')

    def _choose_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.selected_file = path
            self.lbl_file.config(text=f"Fichier: {path.split('/')[-1]}", fg='black')

    def _choose_directory(self):
        path = filedialog.askdirectory()
        if path:
            self.selected_file = path
            self.lbl_file.config(text=f"Dossier: {path.split('/')[-1]}", fg='blue')

    def _send_file(self):
        if not self.selected_file:
            messagebox.showwarning('Erreur', 'Selectionnez un fichier ou dossier')
            return
        ip = self.entry_ip.get().strip()
        if not ip:
            messagebox.showwarning('Erreur', 'Entrez une IP')
            return
        try:
            port = int(self.entry_port.get())
        except ValueError:
            messagebox.showwarning('Erreur', 'Port invalide')
            return
        client = FileClient(callback=self._on_client_event)
        threading.Thread(target=client.send_file, args=(self.selected_file, ip, port), daemon=True).start()

    def _toggle_server(self):
        if self.server and self.server.running:
            self.server.stop()
        else:
            try:
                port = int(self.entry_port_recu.get())
            except ValueError:
                messagebox.showwarning('Erreur', 'Port invalide')
                return
            self.server = FileServer(port, callback=self._on_serveur_event)
            self.server.start()

    def _on_serveur_event(self, event, data=None):
        self.queue.put(('serveur', event, data))

    def _on_client_event(self, event, data=None):
        self.queue.put(('client', event, data))

    def _check_queue(self):
        try:
            while True:
                source, event, data = self.queue.get_nowait()
                if source == 'serveur':
                    if event == 'serveur_demarre':
                        self.btn_serveur.config(text='Arreter serveur')
                        self.lbl_status.config(text='Serveur actif', fg='green')
                    elif event == 'serveur_arrete':
                        self.btn_serveur.config(text='Demarrer serveur')
                        self.lbl_status.config(text='Serveur inactif', fg='red')
                        self.bar_recu['value'] = 0
                    elif event == 'recu_info':
                        self.bar_recu['value'] = 0
                        self.bar_recu.config(maximum=data['taille'])
                        type_str = "Dossier" if data.get('is_dir') else "Fichier"
                        self.lst_recu.insert(tk.END, f"Recu {type_str}: {data['filename']}")
                    elif event == 'progress':
                        self.bar_recu['value'] = data
                    elif event == 'info':
                        self.lst_recu.insert(tk.END, f"INFO: {data}")
                    elif event == 'fini':
                        self.bar_recu['value'] = self.bar_recu['maximum']
                        self.lst_recu.insert(tk.END, f'TERMINE: {data}')
                    elif event == 'erreur':
                        messagebox.showerror('Erreur Flash', str(data))
                elif source == 'client':
                    if event == 'envoi_info':
                        self.bar_envoi['value'] = 0
                        self.bar_envoi.config(maximum=data['taille'])
                    elif event == 'progress':
                        self.bar_envoi['value'] = data
                    elif event == 'info':
                        self.lbl_file.config(text=data, fg='orange')
                    elif event == 'fini':
                        self.bar_envoi['value'] = self.bar_envoi['maximum']
                        messagebox.showinfo('Flash', f'Transfert de {data} réussi !')
                        self.lbl_file.config(text='Aucun fichier', fg='gray')
                        self.selected_file = None
                    elif event == 'erreur':
                        messagebox.showerror('Erreur Flash', str(data))
        except queue.Empty:
            pass
        self.root.after(100, self._check_queue)

    def run(self):
        self.root.mainloop()
