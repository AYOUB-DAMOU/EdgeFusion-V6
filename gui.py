import tkinter as tk
from tkinter import filedialog, messagebox
import uuid
import os
import json
import time
import process
import journal as _journal
from _paths import STATUS_FILE
from config import (
    config_load, config_save,
    config_add_broker, config_update_broker, config_remove_broker,
    config_add_source, config_update_source, config_remove_source,
    config_get_brokers, config_get_sources, config_get_options
)
from certificate import generate_certificate

import threading as _th
def _preload_service():
    try:
        import service
    except Exception:
        pass
_th.Thread(target=_preload_service, daemon=True).start()

# ============================================================
#  COULEURS
# ============================================================
BG        = "#050A18"
BG_WIN    = "#0A1628"
BG_SEC    = "#0D1F3C"
BG_HDR    = "#080F20"
BG_TITLE  = "#112244"
BG_ENTRY  = "#091526"
BORDER    = "#1E3A8A"
TEXT      = "#E3F2FD"
TEXT_DIM  = "#78909C"
TEXT_ACC  = "#90CAF9"
GREEN     = "#4CAF50"
GREEN_BG  = "#0D2B1A"
GREEN_BD  = "#2E7D32"
RED       = "#EF5350"
RED_BG    = "#2B0D0D"
RED_BD    = "#C62828"
ORANGE    = "#FFA726"
ORANGE_BG = "#2B1A0D"
ORANGE_BD = "#E65100"
GRAY      = "#78909C"
GRAY_BG   = "#1A1F2B"
GRAY_BD   = "#37474F"

MDL2      = "Segoe MDL2 Assets"
IC_BOLT   = ""
IC_BROKER = ""
IC_SOURCE = ""
IC_OPT    = ""
IC_FOLDER = ""
IC_LOCK   = ""
IC_ADD    = ""
IC_EDIT   = ""
IC_DEL    = ""

root           = None
_icon_path     = None   # chemin vers appicon.ico
_content_frame = None   # frame intérieure de la zone scrollable

# ============================================================
#  POPUP GENERIQUES
# ============================================================
def show_popup_info(title, message):
    popup = tk.Toplevel(root)
    popup.title(title)
    popup.configure(bg=BG_WIN)
    popup.resizable(False, False)
    popup.grab_set()
    _apply_popup_icon(popup)
    tk.Label(popup, text=message, font=("Arial", 10),
             bg=BG_WIN, fg=TEXT, pady=10, padx=20, justify="center").pack()
    tk.Button(popup, text="  Fermer  ", command=popup.destroy,
              bg=BG_TITLE, fg=TEXT_ACC, relief="flat",
              highlightthickness=1, highlightbackground=BORDER,
              pady=5, cursor="hand2").pack(pady=10)

def show_popup_error(title, message):
    popup = tk.Toplevel(root)
    popup.title(title)
    popup.configure(bg=BG_WIN)
    popup.resizable(False, False)
    popup.grab_set()
    _apply_popup_icon(popup)
    tk.Label(popup, text="❌  " + title, font=("Arial", 11, "bold"),
             bg=BG_WIN, fg=RED, pady=8, padx=20).pack()
    tk.Label(popup, text=message, font=("Arial", 10),
             bg=BG_WIN, fg=TEXT, pady=5, padx=20, justify="center").pack()
    tk.Button(popup, text="  Fermer  ", command=popup.destroy,
              bg=RED_BG, fg=RED, relief="flat",
              highlightthickness=1, highlightbackground=RED_BD,
              pady=5, cursor="hand2").pack(pady=10)

def show_popup_confirm(title, message, on_confirm):
    popup = tk.Toplevel(root)
    popup.title(title)
    popup.configure(bg=BG_WIN)
    popup.resizable(False, False)
    popup.grab_set()
    _apply_popup_icon(popup)
    tk.Label(popup, text=message, font=("Arial", 10),
             bg=BG_WIN, fg=TEXT, pady=10, padx=20, justify="center").pack()
    btn_frame = tk.Frame(popup, bg=BG_WIN)
    btn_frame.pack(pady=10)
    def _confirm():
        popup.destroy()
        on_confirm()
    tk.Button(btn_frame, text="  Confirmer  ", command=_confirm,
              bg=RED_BG, fg=RED, relief="flat",
              highlightthickness=1, highlightbackground=RED_BD,
              pady=5, cursor="hand2").pack(side="left", padx=5)
    tk.Button(btn_frame, text="  Annuler  ", command=popup.destroy,
              bg=BG_TITLE, fg=TEXT_ACC, relief="flat",
              highlightthickness=1, highlightbackground=BORDER,
              pady=5, cursor="hand2").pack(side="left", padx=5)

# ============================================================
#  HELPERS GUI
# ============================================================
def _make_field(parent, row, label_text, show="", default=""):
    tk.Label(parent, text=label_text, font=("Arial", 9),
             bg=BG_SEC, fg=TEXT_DIM, width=12, anchor="e").grid(
                 row=row, column=0, padx=(0, 8), pady=3, sticky="e")
    e = tk.Entry(parent, show=show, font=("Arial", 9),
                 bg=BG_ENTRY, fg=TEXT, insertbackground=TEXT,
                 relief="flat", highlightthickness=1,
                 highlightbackground=BORDER, highlightcolor=TEXT_ACC)
    if default:
        e.insert(0, default)
    e.grid(row=row, column=1, pady=3, sticky="ew")
    return e

def _section_header(parent, title, icon=""):
    th = tk.Frame(parent, bg=BG_TITLE)
    th.pack(fill="x")
    tk.Frame(th, bg=TEXT_ACC, width=4).pack(side="left", fill="y")
    if icon:
        tk.Label(th, text=icon, font=(MDL2, 13),
                 bg=BG_TITLE, fg=TEXT_ACC, padx=8).pack(side="left")
    tk.Label(th, text=title, font=("Arial", 10, "bold"),
             bg=BG_TITLE, fg=TEXT_ACC, pady=6, padx=4).pack(side="left")
    tk.Frame(parent, bg=BORDER, height=1).pack(fill="x")

def _make_btn(parent, text, cmd, bg=BG_TITLE, fg=TEXT_ACC, bd=BORDER):
    return tk.Button(parent, text=text, command=cmd,
                     bg=bg, fg=fg, font=("Arial", 9),
                     relief="flat", highlightthickness=1,
                     highlightbackground=bd, cursor="hand2",
                     padx=8, pady=4)

# ============================================================
#  POPUP CONFIG BROKER
# ============================================================
def open_broker_config(broker_id=None):
    brokers   = config_get_brokers()
    broker    = next((b for b in brokers if b["id"] == broker_id), None)
    is_new    = broker is None

    popup = tk.Toplevel(root)
    popup.title("Nouveau Broker" if is_new else "Modifier Broker")
    popup.configure(bg=BG_WIN)
    popup.resizable(False, False)
    popup.grab_set()
    _apply_popup_icon(popup)

    # Header
    ph = tk.Frame(popup, bg=BG_TITLE, pady=10)
    ph.pack(fill="x")
    tk.Label(ph, text=IC_BROKER, font=(MDL2, 24),
             bg=BG_TITLE, fg=TEXT_ACC).pack()
    tk.Label(ph, text="Configuration Broker MQTT",
             font=("Arial", 11, "bold"), bg=BG_TITLE, fg=TEXT_ACC).pack()
    tk.Frame(ph, bg=BORDER, height=1).pack(fill="x", pady=(8, 0))

    body = tk.Frame(popup, bg=BG_SEC, padx=20, pady=12)
    body.pack(fill="x")
    body.columnconfigure(1, weight=1)

    e_name = _make_field(body, 0, "Nom",  default=broker.get("name", "") if broker else "")
    e_host = _make_field(body, 1, "Host", default=broker.get("host", "") if broker else "")
    e_port = _make_field(body, 2, "Port", default=broker.get("port", "1883") if broker else "1883")

    # ── TLS / MQTTS ──
    tls_sep = tk.Frame(body, bg=BORDER, height=1)
    tls_sep.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 4))

    tls_var = tk.BooleanVar(value=broker.get("tls", False) if broker else False)

    def _on_tls_toggle():
        state = "normal" if tls_var.get() else "disabled"
        e_ca.config(state=state)
        btn_ca.config(state=state)
        e_ccert.config(state=state)
        btn_ccert.config(state=state)
        e_ckey.config(state=state)
        btn_ckey.config(state=state)
        insecure_cb.config(state=state)
        if tls_var.get() and e_port.get().strip() == "1883":
            e_port.delete(0, "end")
            e_port.insert(0, "8883")
        elif not tls_var.get() and e_port.get().strip() == "8883":
            e_port.delete(0, "end")
            e_port.insert(0, "1883")

    tk.Checkbutton(
        body, text="  MQTTS (TLS/SSL)", variable=tls_var,
        command=_on_tls_toggle, bg=BG_SEC, fg=TEXT_ACC,
        selectcolor=BG_ENTRY, activebackground=BG_SEC,
        font=("Arial", 9, "bold")
    ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(2, 4))

    def _browse_file(entry_widget):
        path = filedialog.askopenfilename(
            parent=popup,
            filetypes=[("Certificats", "*.pem *.crt *.cer *.key"), ("Tous", "*.*")]
        )
        if path:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, path)

    tk.Label(body, text="Certificat CA", font=("Arial", 9),
             bg=BG_SEC, fg=TEXT_DIM).grid(row=5, column=0, sticky="e", padx=(0, 8), pady=2)
    ca_frame = tk.Frame(body, bg=BG_SEC)
    ca_frame.grid(row=5, column=1, sticky="ew", pady=2)
    e_ca = tk.Entry(ca_frame, bg=BG_ENTRY, fg=TEXT, insertbackground=TEXT,
                    font=("Arial", 9), relief="flat", highlightthickness=1,
                    highlightbackground=BORDER)
    e_ca.pack(side="left", fill="x", expand=True)
    e_ca.insert(0, broker.get("ca_cert", "") if broker else "")
    btn_ca = tk.Button(ca_frame, text="...", command=lambda: _browse_file(e_ca),
                       bg=BG_TITLE, fg=TEXT_ACC, relief="flat", cursor="hand2", width=3)
    btn_ca.pack(side="right", padx=(4, 0))

    tk.Label(body, text="Cert client", font=("Arial", 9),
             bg=BG_SEC, fg=TEXT_DIM).grid(row=6, column=0, sticky="e", padx=(0, 8), pady=2)
    cc_frame = tk.Frame(body, bg=BG_SEC)
    cc_frame.grid(row=6, column=1, sticky="ew", pady=2)
    e_ccert = tk.Entry(cc_frame, bg=BG_ENTRY, fg=TEXT, insertbackground=TEXT,
                       font=("Arial", 9), relief="flat", highlightthickness=1,
                       highlightbackground=BORDER)
    e_ccert.pack(side="left", fill="x", expand=True)
    e_ccert.insert(0, broker.get("client_cert", "") if broker else "")
    btn_ccert = tk.Button(cc_frame, text="...", command=lambda: _browse_file(e_ccert),
                          bg=BG_TITLE, fg=TEXT_ACC, relief="flat", cursor="hand2", width=3)
    btn_ccert.pack(side="right", padx=(4, 0))

    tk.Label(body, text="Clé client", font=("Arial", 9),
             bg=BG_SEC, fg=TEXT_DIM).grid(row=7, column=0, sticky="e", padx=(0, 8), pady=2)
    ck_frame = tk.Frame(body, bg=BG_SEC)
    ck_frame.grid(row=7, column=1, sticky="ew", pady=2)
    e_ckey = tk.Entry(ck_frame, bg=BG_ENTRY, fg=TEXT, insertbackground=TEXT,
                      font=("Arial", 9), relief="flat", highlightthickness=1,
                      highlightbackground=BORDER)
    e_ckey.pack(side="left", fill="x", expand=True)
    e_ckey.insert(0, broker.get("client_key", "") if broker else "")
    btn_ckey = tk.Button(ck_frame, text="...", command=lambda: _browse_file(e_ckey),
                         bg=BG_TITLE, fg=TEXT_ACC, relief="flat", cursor="hand2", width=3)
    btn_ckey.pack(side="right", padx=(4, 0))

    insecure_var = tk.BooleanVar(value=broker.get("tls_insecure", False) if broker else False)
    insecure_cb = tk.Checkbutton(
        body, text="  Ignorer vérification certificat serveur", variable=insecure_var,
        bg=BG_SEC, fg=ORANGE, selectcolor=BG_ENTRY, activebackground=BG_SEC,
        font=("Arial", 8)
    )
    insecure_cb.grid(row=8, column=0, columnspan=2, sticky="w", pady=2)

    # Etat initial des champs TLS
    init_state = "normal" if tls_var.get() else "disabled"
    for w in (e_ca, btn_ca, e_ccert, btn_ccert, e_ckey, btn_ckey, insecure_cb):
        w.config(state=init_state)

    lbl_err = tk.Label(body, text="", font=("Arial", 9), bg=BG_SEC, fg=RED)
    lbl_err.grid(row=9, column=0, columnspan=2, pady=2)

    def _save():
        name = e_name.get().strip()
        host = e_host.get().strip()
        if not name or not host:
            lbl_err.config(text="Nom et Host sont obligatoires")
            return
        b = {
            "id":           broker_id if broker_id else str(uuid.uuid4())[:8],
            "name":         name,
            "host":         host,
            "port":         e_port.get().strip() or "1883",
            "tls":          tls_var.get(),
            "ca_cert":      e_ca.get().strip(),
            "client_cert":  e_ccert.get().strip(),
            "client_key":   e_ckey.get().strip(),
            "tls_insecure": insecure_var.get(),
        }
        if is_new:
            config_add_broker(b)
        else:
            config_update_broker(broker_id, b)
        popup.destroy()
        update_brokers_list()

    tk.Button(body, text="  Enregistrer", font=("Arial", 10, "bold"),
              bg=GREEN_BG, fg=GREEN, relief="flat",
              highlightthickness=1, highlightbackground=GREEN_BD,
              command=_save, cursor="hand2", pady=8).grid(
                  row=10, column=0, columnspan=2, sticky="ew", pady=(8, 0))

# ============================================================
#  POPUP CONFIG SOURCE
# ============================================================
def open_source_config(source_id=None):
    sources  = config_get_sources()
    brokers  = config_get_brokers()
    source   = next((s for s in sources if s["id"] == source_id), None)
    is_new   = source is None

    if not brokers:
        show_popup_error("Erreur", "Ajoutez au moins un broker MQTT d'abord")
        return

    popup = tk.Toplevel(root)
    popup.title("Nouvelle Source" if is_new else "Modifier Source")
    popup.configure(bg=BG_WIN)
    popup.resizable(False, False)
    popup.grab_set()
    _apply_popup_icon(popup)

    # Header
    ph = tk.Frame(popup, bg=BG_TITLE, pady=10)
    ph.pack(fill="x")
    tk.Label(ph, text=IC_SOURCE, font=(MDL2, 24),
             bg=BG_TITLE, fg=TEXT_ACC).pack()
    tk.Label(ph, text="Configuration Source OPC UA",
             font=("Arial", 11, "bold"), bg=BG_TITLE, fg=TEXT_ACC).pack()
    tk.Frame(ph, bg=BORDER, height=1).pack(fill="x", pady=(8, 0))

    body = tk.Frame(popup, bg=BG_SEC, padx=20, pady=12)
    body.pack(fill="x")
    body.columnconfigure(1, weight=1)

    # ── Section OPC UA ──────────────────────────────────────────
    tk.Label(body, text="— OPC UA —", font=("Arial", 8, "bold"),
             bg=BG_SEC, fg=TEXT_ACC).grid(row=0, column=0, columnspan=2, pady=(4, 2))

    e_name = _make_field(body, 1, "Nom",      default=source.get("name",     "") if source else "")
    e_ip   = _make_field(body, 2, "OPC IP",   default=source.get("opc_ip",   "") if source else "")
    e_opc_port = _make_field(body, 3, "OPC Port", default=source.get("opc_port", "4840") if source else "4840")
    e_opc_user = _make_field(body, 4, "OPC Login",  default=source.get("opc_user", "") if source else "")
    e_opc_pass = _make_field(body, 5, "OPC MDP", show="*", default=source.get("opc_pass", "") if source else "")

    # ── Section MQTT Device ──────────────────────────────────────
    tk.Label(body, text="— MQTT Device —", font=("Arial", 8, "bold"),
             bg=BG_SEC, fg=TEXT_ACC).grid(row=6, column=0, columnspan=2, pady=(10, 2))

    e_topic     = _make_field(body,  7, "Topic",     default=source.get("topic",     "") if source else "")
    e_client    = _make_field(body,  8, "Client ID", default=source.get("client_id", "") if source else "")
    e_mqtt_user = _make_field(body,  9, "MQTT Login",  default=source.get("mqtt_user", "") if source else "")
    e_mqtt_pass = _make_field(body, 10, "MQTT MDP", show="*", default=source.get("mqtt_pass", "") if source else "")
    e_qos       = _make_field(body, 11, "QoS",       default=str(source.get("qos", 1)) if source else "1")

    # ── Excel ────────────────────────────────────────────────────
    tk.Label(body, text="— Fichier ─", font=("Arial", 8, "bold"),
             bg=BG_SEC, fg=TEXT_ACC).grid(row=12, column=0, columnspan=2, pady=(10, 2))

    tk.Label(body, text="Excel", font=("Arial", 9),
             bg=BG_SEC, fg=TEXT_DIM, width=12, anchor="e").grid(
                 row=13, column=0, padx=(0, 8), pady=3, sticky="e")
    excel_frame = tk.Frame(body, bg=BG_SEC)
    excel_frame.grid(row=13, column=1, pady=3, sticky="ew")
    excel_path_var = tk.StringVar(value=source.get("excel_path", "") if source else "")
    tk.Label(excel_frame, textvariable=excel_path_var, font=("Arial", 8),
             bg=BG_ENTRY, fg=TEXT_ACC, anchor="w", width=22).pack(side="left", fill="x", expand=True)
    def _browse():
        p = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
        if p:
            excel_path_var.set(p)
    tk.Button(excel_frame, text=IC_FOLDER, font=(MDL2, 10),
              bg=BG_TITLE, fg=TEXT_ACC, relief="flat",
              highlightthickness=1, highlightbackground=BORDER,
              command=_browse, cursor="hand2", padx=6).pack(side="right")

    # ── Brokers (multi-sélection) ──────────────────────────────────
    tk.Label(body, text="— Brokers —", font=("Arial", 8, "bold"),
             bg=BG_SEC, fg=TEXT_ACC).grid(row=14, column=0, columnspan=2, pady=(10, 2))

    broker_frame = tk.Frame(body, bg=BG_ENTRY, highlightthickness=1, highlightbackground=BORDER)
    broker_frame.grid(row=15, column=0, columnspan=2, pady=3, sticky="ew")

    # Récupérer les broker_ids déjà sélectionnés (V6: broker_ids, rétro-compat: broker_id)
    existing_bids = []
    if source:
        existing_bids = source.get("broker_ids", [])
        if not existing_bids and source.get("broker_id"):
            existing_bids = [source["broker_id"]]

    broker_vars = {}
    for b in brokers:
        var = tk.IntVar(value=1 if b["id"] in existing_bids else 0)
        broker_vars[b["id"]] = var
        proto = "MQTTS" if b.get("tls") else "MQTT"
        cb = tk.Checkbutton(
            broker_frame, text=f"{b['name']}  ({b['host']}:{b['port']} [{proto}])",
            variable=var, font=("Arial", 9),
            bg=BG_ENTRY, fg=TEXT, selectcolor=BG_SEC,
            activebackground=BG_ENTRY, activeforeground=TEXT_ACC,
            anchor="w", padx=6, pady=2
        )
        cb.pack(fill="x")

    lbl_err = tk.Label(body, text="", font=("Arial", 9), bg=BG_SEC, fg=RED)
    lbl_err.grid(row=16, column=0, columnspan=2, pady=2)

    def _save():
        name  = e_name.get().strip()
        ip    = e_ip.get().strip()
        excel = excel_path_var.get().strip()
        if not name or not ip or not excel:
            lbl_err.config(text="Nom, OPC IP et Excel sont obligatoires")
            return
        selected_bids = [bid for bid, var in broker_vars.items() if var.get() == 1]
        if not selected_bids:
            lbl_err.config(text="Sélectionnez au moins un broker")
            return
        opc_port = e_opc_port.get().strip() or "4840"
        s = {
            "id":         source_id if source_id else str(uuid.uuid4())[:8],
            "name":       name,
            "opc_ip":     ip,
            "opc_port":   opc_port,
            "opc_url":    f"opc.tcp://{ip}:{opc_port}",
            "opc_user":   e_opc_user.get().strip(),
            "opc_pass":   e_opc_pass.get(),
            "excel_path": excel,
            "topic":      e_topic.get().strip(),
            "client_id":  e_client.get().strip(),
            "mqtt_user":  e_mqtt_user.get().strip(),
            "mqtt_pass":  e_mqtt_pass.get(),
            "qos":        int(e_qos.get().strip() or "1"),
            "broker_ids": selected_bids
        }
        if is_new:
            config_add_source(s)
        else:
            config_update_source(source_id, s)
        popup.destroy()
        update_sources_list()

    tk.Button(body, text="✔  Enregistrer", font=("Arial", 10, "bold"),
              bg=GREEN_BG, fg=GREEN, relief="flat",
              highlightthickness=1, highlightbackground=GREEN_BD,
              command=_save, cursor="hand2", pady=8).grid(
                  row=17, column=0, columnspan=2, sticky="ew", pady=(8, 0))

# ============================================================
#  POPUP AUTH — GÉNÉRIQUE (Stop / Quitter)
# ============================================================
def _auth_popup(title, subtitle, btn_text, btn_bg, btn_bd, btn_fg, on_confirmed):
    """
    Popup d'authentification générique.
    - Si login/mdp configurés  → champs login + mot de passe obligatoires
    - Si aucun login/mdp       → simple popup de confirmation (bouton Confirmer)
    Toujours affichée — jamais ignorée.
    """
    cfg           = config_load()
    stop_login    = cfg.get("stop_login", "").strip()
    stop_password = cfg.get("stop_password", "").strip()
    has_creds     = bool(stop_login and stop_password)

    popup = tk.Toplevel(root)
    popup.title(title)
    popup.configure(bg=BG_WIN)
    popup.resizable(False, False)
    popup.grab_set()
    _apply_popup_icon(popup)

    # Header
    ph = tk.Frame(popup, bg=BG_TITLE, pady=12)
    ph.pack(fill="x")
    tk.Label(ph, text=IC_LOCK, font=(MDL2, 32),
             bg=BG_TITLE, fg=TEXT_ACC).pack()
    tk.Label(ph, text=title,
             font=("Arial", 11, "bold"), bg=BG_TITLE, fg=TEXT_ACC).pack()
    tk.Label(ph, text=subtitle,
             font=("Arial", 8), bg=BG_TITLE, fg=TEXT_DIM).pack(pady=(2, 0))
    tk.Frame(ph, bg=BORDER, height=1).pack(fill="x", pady=(8, 0))

    body = tk.Frame(popup, bg=BG_SEC, padx=20, pady=12)
    body.pack(fill="x")
    body.columnconfigure(1, weight=1)

    if has_creds:
        # Mode avec credentials : champs login + mot de passe
        e_login = _make_field(body, 0, "Login")
        e_login.focus()
        e_pass  = _make_field(body, 1, "Mot de passe", show="*")
        lbl_err = tk.Label(body, text="", font=("Arial", 9), bg=BG_SEC, fg=RED)
        lbl_err.grid(row=2, column=0, columnspan=2)

        def _confirm():
            if e_login.get() == stop_login and e_pass.get() == stop_password:
                popup.destroy()
                on_confirmed()
            else:
                lbl_err.config(text="⚠  Login ou mot de passe incorrect")

        e_pass.bind("<Return>", lambda e: _confirm())
        btn_row = 3

    else:
        # Mode sans credentials : simple confirmation
        tk.Label(body, text="Confirmer cette action ?",
                 font=("Arial", 10), bg=BG_SEC, fg=TEXT,
                 pady=8).grid(row=0, column=0, columnspan=2)

        def _confirm():
            popup.destroy()
            on_confirmed()

        btn_row = 1

    # Boutons Confirmer + Annuler
    btns = tk.Frame(body, bg=BG_SEC)
    btns.grid(row=btn_row, column=0, columnspan=2, sticky="ew", pady=(8, 0))
    btns.columnconfigure(0, weight=1)
    btns.columnconfigure(1, weight=1)

    tk.Button(btns, text=btn_text, font=("Arial", 10, "bold"),
              bg=btn_bg, fg=btn_fg, relief="flat",
              highlightthickness=1, highlightbackground=btn_bd,
              command=_confirm, cursor="hand2", pady=8).grid(
                  row=0, column=0, sticky="ew", padx=(0, 4))

    tk.Button(btns, text="✖  Annuler", font=("Arial", 10),
              bg=BG_TITLE, fg=TEXT_DIM, relief="flat",
              highlightthickness=1, highlightbackground=BORDER,
              command=popup.destroy, cursor="hand2", pady=8).grid(
                  row=0, column=1, sticky="ew", padx=(4, 0))


# ============================================================
#  POPUP AUTH STOP
# ============================================================
def open_stop_auth_popup(on_confirmed):
    """Popup STOP — toujours affichée."""
    _auth_popup(
        title      = "ARRÊTER LES BRIDGES",
        subtitle   = "Cette action arrêtera tous les bridges OPC→MQTT",
        btn_text   = "⏹  Arrêter",
        btn_bg     = RED_BG,
        btn_bd     = RED_BD,
        btn_fg     = RED,
        on_confirmed = on_confirmed
    )

# ============================================================
#  POPUP AUTH MODIFIER (Broker / Source)
# ============================================================
def open_edit_auth_popup(item_label, on_confirmed):
    """
    Popup de modification protégée — toujours affichée.
    item_label : ex. "le broker 'Usine A'" ou "la source 'PCS7'"
    """
    _auth_popup(
        title        = "MODIFIER UN ÉLÉMENT",
        subtitle     = f"Modifier {item_label} ?",
        btn_text     = f"{IC_EDIT}  Modifier",
        btn_bg       = BG_TITLE,
        btn_bd       = BORDER,
        btn_fg       = TEXT_ACC,
        on_confirmed = on_confirmed
    )

# ============================================================
#  POPUP AUTH SUPPRIMER (Broker / Source)
# ============================================================
def open_delete_auth_popup(item_label, on_confirmed):
    """
    Popup de suppression protégée — toujours affichée.
    item_label : ex. "le broker 'Usine A'" ou "la source 'PCS7'"
    """
    _auth_popup(
        title        = "SUPPRIMER UN ÉLÉMENT",
        subtitle     = f"Supprimer {item_label} ?",
        btn_text     = f"{IC_DEL}  Supprimer",
        btn_bg       = RED_BG,
        btn_bd       = RED_BD,
        btn_fg       = RED,
        on_confirmed = on_confirmed
    )

# ============================================================
#  LISTES (brokers + sources)
# ============================================================
_brokers_frame  = None
_sources_frame  = None
_source_widgets = {}   # {source_id: {"opc_dot": lbl, "mqtt_dot": lbl}} — mis à jour sans recréer

def update_brokers_list():
    """Rafraîchit la liste des brokers dans la GUI."""
    if _brokers_frame is None:
        return
    for w in _brokers_frame.winfo_children():
        w.destroy()
    brokers = config_get_brokers()
    if not brokers:
        tk.Label(_brokers_frame, text="Aucun broker configuré",
                 font=("Arial", 9), bg=BG_SEC, fg=TEXT_DIM).pack(pady=6)
        return
    for b in brokers:
        row = tk.Frame(_brokers_frame, bg=BG_SEC)
        row.pack(fill="x", pady=2)
        tk.Label(row, text=IC_BROKER, font=(MDL2, 11),
                 bg=BG_SEC, fg=TEXT_ACC, padx=6).pack(side="left")
        proto = "MQTTS" if b.get("tls") else "MQTT"
        tk.Label(row, text=f"{b['name']}  —  {b['host']}:{b['port']}  [{proto}]",
                 font=("Arial", 9), bg=BG_SEC, fg=TEXT).pack(side="left", fill="x", expand=True)
        _make_btn(row, IC_EDIT,
                  lambda bid=b["id"], bname=b["name"]: open_edit_auth_popup(
                      f"le broker '{bname}'",
                      lambda: open_broker_config(bid)),
                  fg=TEXT_ACC).pack(side="right", padx=2)
        _make_btn(row, IC_DEL,
                  lambda bid=b["id"], bname=b["name"]: open_delete_auth_popup(
                      f"le broker '{bname}'",
                      lambda: [config_remove_broker(bid), update_brokers_list()]),
                  fg=RED, bd=RED_BD).pack(side="right", padx=2)

def update_sources_list():
    """
    Rafraîchit la liste des sources.
    - Rebuild complet uniquement si la liste de sources a changé.
    - Sinon : mise à jour des couleurs OPC/MQTT par .configure() — sans flickering.
    """
    global _source_widgets
    if _sources_frame is None:
        return

    sources     = config_get_sources()
    brokers_map = {b["id"]: b["name"] for b in config_get_brokers()}
    cur_sig     = [(s["id"], s.get("name",""), s.get("opc_ip",""),
                    ",".join(s.get("broker_ids", [s.get("broker_id","")])),
                    os.path.basename(s.get("excel_path","")))
                   for s in sources]

    # ---- Rebuild si la liste OU les noms/IPs ont changé ----
    _prev = getattr(update_sources_list, "_prev_sig", None)
    update_sources_list._prev_sig = cur_sig
    if cur_sig != _prev:
        for w in _sources_frame.winfo_children():
            w.destroy()
        _source_widgets.clear()

        if not sources:
            tk.Label(_sources_frame, text="Aucune source configurée",
                     font=("Arial", 9), bg=BG_SEC, fg=TEXT_DIM).pack(pady=6)
            return

        for s in sources:
            bid_list = s.get("broker_ids", [s.get("broker_id", "")])
            broker_name = ", ".join(brokers_map.get(bid, "?") for bid in bid_list if bid)

            row = tk.Frame(_sources_frame, bg=BG_SEC, pady=3)
            row.pack(fill="x")
            info = tk.Frame(row, bg=BG_SEC)
            info.pack(side="left", fill="x", expand=True)

            name_row = tk.Frame(info, bg=BG_SEC)
            name_row.pack(fill="x")

            opc_dot = tk.Label(name_row, text="●", font=("Arial", 9),
                               bg=BG_SEC, fg=RED)
            opc_dot.pack(side="left", padx=(6, 2))
            tk.Label(name_row, text=s["name"],
                     font=("Arial", 9, "bold"), bg=BG_SEC, fg=TEXT).pack(side="left")
            tk.Label(name_row, text=f"  {s['opc_ip']}",
                     font=("Arial", 9), bg=BG_SEC, fg=TEXT_DIM).pack(side="left")
            mqtt_dot = tk.Label(name_row, text="●", font=("Arial", 8),
                                bg=BG_SEC, fg=RED)
            mqtt_dot.pack(side="right", padx=6)

            sub_row = tk.Frame(info, bg=BG_SEC)
            sub_row.pack(fill="x")
            tk.Label(sub_row,
                     text=f"   └─ {broker_name}  |  {os.path.basename(s.get('excel_path',''))}",
                     font=("Arial", 8), bg=BG_SEC, fg=TEXT_DIM).pack(side="left")

            tk.Frame(_sources_frame, bg=BORDER, height=1).pack(fill="x")

            _make_btn(row, IC_EDIT,
                      lambda sid=s["id"], sname=s["name"]: open_edit_auth_popup(
                          f"la source '{sname}'",
                          lambda: open_source_config(sid)),
                      fg=TEXT_ACC).pack(side="right", padx=2)
            _make_btn(row, IC_DEL,
                      lambda sid=s["id"], sname=s["name"]: open_delete_auth_popup(
                          f"la source '{sname}'",
                          lambda: [config_remove_source(sid), update_sources_list()]),
                      fg=RED, bd=RED_BD).pack(side="right", padx=2)

            _source_widgets[s["id"]] = {"opc_dot": opc_dot, "mqtt_dot": mqtt_dot}

    # ---- Mise à jour couleurs uniquement (pas de recréation) ----
    all_statuses = _get_sources_status()
    for s in sources:
        w = _source_widgets.get(s["id"])
        if not w:
            continue
        st = all_statuses.get(s["id"], {})
        w["opc_dot"].configure(fg=GREEN if st.get("opc")  == "CONNECTED" else RED)
        w["mqtt_dot"].configure(fg=GREEN if st.get("mqtt_global", st.get("mqtt")) == "CONNECTED" else RED)

# ============================================================
#  BARRE DE STATUT OPC / MQTT
# ============================================================
_status_bar_frame = None
_blink_on         = True
_status_widgets   = {}   # {source_id: {frames + labels}} — mis à jour sans recréer

def build_status_bar(parent):
    """Construit la barre de statut globale OPC + MQTT."""
    global _status_bar_frame

    sb_outer = tk.Frame(parent, bg=BG_SEC, pady=2)
    sb_outer.pack(fill="x")

    _status_bar_frame = tk.Frame(sb_outer, bg=BG_SEC)
    _status_bar_frame.pack(fill="x", padx=14, pady=4)

    tk.Frame(parent, bg=BORDER, height=1).pack(fill="x")
    update_status_bar()

def update_status_bar():
    """
    Met à jour les pastilles de statut.
    - Rebuild complet uniquement si la liste de sources a changé.
    - Sinon : .configure() uniquement — aucun flickering.
    """
    global _blink_on, _status_bar_frame, _status_widgets
    if _status_bar_frame is None:
        return

    _blink_on = not _blink_on
    statuses  = _get_sources_status()
    sources   = config_get_sources()
    cur_sig   = [(s["id"], s.get("name","")) for s in sources]

    # ---- Rebuild si la liste OU les noms ont changé ----
    _prev = getattr(update_status_bar, "_prev_sig", None)
    update_status_bar._prev_sig = cur_sig
    if cur_sig != _prev:
        for w in _status_bar_frame.winfo_children():
            w.destroy()
        _status_widgets.clear()

        if not sources:
            tk.Label(_status_bar_frame, text="Aucune source configurée",
                     font=("Arial", 8), bg=BG_SEC, fg=TEXT_DIM).pack(side="left", padx=6)
            return

        for i, s in enumerate(sources):
            src_frame = tk.Frame(_status_bar_frame, bg=BG_SEC)
            src_frame.pack(fill="x", pady=2)

            tk.Label(src_frame, text=s["name"],
                     font=("Arial", 8, "bold"), bg=BG_SEC,
                     fg=TEXT_ACC, width=10, anchor="w").pack(side="left", padx=(4, 6))

            def _make_pill(parent, init_bg, init_bd):
                f = tk.Frame(parent, bg=init_bg,
                             highlightbackground=init_bd, highlightthickness=1)
                dot = tk.Label(f, text="●", font=("Arial", 7),
                               bg=init_bg, fg=RED)
                dot.pack(side="left", padx=(6, 1), pady=4)
                lbl = tk.Label(f, text="---", font=("Arial", 8, "bold"),
                               bg=init_bg, fg=RED)
                lbl.pack(side="left", padx=(0, 7), pady=4)
                return f, dot, lbl

            opc_f,  opc_dot,  opc_lbl  = _make_pill(src_frame, RED_BG,    RED_BD)
            opc_f.pack(side="left", padx=3)
            mqtt_f, mqtt_dot, mqtt_lbl = _make_pill(src_frame, RED_BG,    RED_BD)
            mqtt_f.pack(side="left", padx=3)
            buf_f,  buf_dot,  buf_lbl  = _make_pill(src_frame, GRAY_BG,   GRAY_BD)
            buf_f.pack(side="left", padx=3)

            last_lbl = tk.Label(src_frame, text="",
                                font=("Arial", 7), bg=BG_SEC, fg=TEXT_DIM)
            last_lbl.pack(side="left", padx=4)

            if i < len(sources) - 1:
                tk.Frame(_status_bar_frame, bg=BORDER, height=1).pack(fill="x", pady=2)

            _status_widgets[s["id"]] = {
                "opc_f":  opc_f,  "opc_dot":  opc_dot,  "opc_lbl":  opc_lbl,
                "mqtt_f": mqtt_f, "mqtt_dot": mqtt_dot, "mqtt_lbl": mqtt_lbl,
                "buf_f":  buf_f,  "buf_dot":  buf_dot,  "buf_lbl":  buf_lbl,
                "last_lbl": last_lbl,
            }

    # ---- Mise à jour couleurs/textes uniquement (pas de recréation) ----
    for s in sources:
        sid = s["id"]
        w   = _status_widgets.get(sid)
        if not w:
            continue
        st = statuses.get(sid, {})

        opc_ok    = st.get("opc")    == "CONNECTED"
        mqtt_ok   = st.get("mqtt_global", st.get("mqtt")) == "CONNECTED"
        buf_ok    = st.get("buffer") == "OPERATIONNEL"
        buf_count = st.get("buffer_count", 0)

        # Calcul couleurs
        opc_fg   = GREEN  if opc_ok  else RED
        opc_bg   = GREEN_BG if opc_ok  else RED_BG
        opc_bd   = GREEN_BD if opc_ok  else RED_BD
        opc_dot  = (GREEN  if _blink_on else GREEN_BG)  if opc_ok  else RED

        mqtt_fg  = GREEN  if mqtt_ok else RED
        mqtt_bg  = GREEN_BG if mqtt_ok else RED_BG
        mqtt_bd  = GREEN_BD if mqtt_ok else RED_BD
        mqtt_dot = (GREEN  if _blink_on else GREEN_BG)  if mqtt_ok else RED

        buf_fg   = ORANGE if buf_ok  else GRAY
        buf_bg   = ORANGE_BG if buf_ok else GRAY_BG
        buf_bd   = ORANGE_BD if buf_ok else GRAY_BD
        buf_dot  = (ORANGE if _blink_on else ORANGE_BG) if buf_ok  else GRAY

        opc_text  = "OPC: CONNECTÉ"   if opc_ok  else "OPC: DÉCONNECTÉ"
        mqtt_text = "MQTT: CONNECTÉ"  if mqtt_ok else "MQTT: DÉCONNECTÉ"
        buf_text  = f"BUFFER: ACTIF ({buf_count})" if buf_ok else "BUFFER: INACTIF"

        # Appliquer sans détruire les widgets
        w["opc_f"].configure( bg=opc_bg,  highlightbackground=opc_bd)
        w["opc_dot"].configure( bg=opc_bg,  fg=opc_dot)
        w["opc_lbl"].configure( bg=opc_bg,  fg=opc_fg,  text=opc_text)

        w["mqtt_f"].configure(bg=mqtt_bg, highlightbackground=mqtt_bd)
        w["mqtt_dot"].configure(bg=mqtt_bg, fg=mqtt_dot)
        w["mqtt_lbl"].configure(bg=mqtt_bg, fg=mqtt_fg, text=mqtt_text)

        w["buf_f"].configure( bg=buf_bg,  highlightbackground=buf_bd)
        w["buf_dot"].configure( bg=buf_bg,  fg=buf_dot)
        w["buf_lbl"].configure( bg=buf_bg,  fg=buf_fg,  text=buf_text)

        last = st.get("last_data", "")
        w["last_lbl"].configure(text=f"  {last}" if last else "")

# ============================================================
#  BOUCLE UPDATE STATUS
# ============================================================
def update_loop():
    """Rafraîchit la liste des sources, la barre de statut et le journal toutes les secondes."""
    update_sources_list()
    update_status_bar()
    _refresh_journal()
    root.after(1000, update_loop)

# ============================================================
#  START / STOP
# ============================================================
def _is_service_active():
    """Retourne True si le fichier status.json existe et a été mis à jour il y a moins de 20s."""
    try:
        if os.path.exists(STATUS_FILE):
            return time.time() - os.path.getmtime(STATUS_FILE) < 20
    except Exception:
        pass
    return False

def _get_sources_status():
    """Retourne le statut des sources : depuis fichier si service actif, sinon mémoire."""
    if _is_service_active():
        try:
            with open(STATUS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return process.get_sources_status()

# ============================================================
def _service_installed():
    """Retourne True si le service Windows EdgeFusion est installé."""
    try:
        from service import service_status
        return service_status() in ("RUNNING", "STOPPED")
    except Exception:
        return False

def _do_start():
    sources = config_get_sources()
    brokers = config_get_brokers()
    options = config_get_options()
    if not sources:
        show_popup_error("Erreur", "Ajoutez au moins une source OPC UA")
        return
    if not brokers:
        show_popup_error("Erreur", "Ajoutez au moins un broker MQTT")
        return
    btn_start.config(bg="#2E7D32")
    btn_stop.config(bg=RED_BD)

    def _init_and_start():
        try:
            process.popup_callback = lambda t, m: root.after(0, lambda: show_popup_info(t, m))
            process.start_all_sources(sources, brokers, options)
            generate_certificate(
                on_success=lambda msg: root.after(0, lambda: show_popup_info("Certificat OPC UA", msg))
            )
        except Exception as e:
            from logger import get_logger
            get_logger("gui").error(f"[START] Erreur démarrage : {e}")
            root.after(0, lambda: show_popup_error("Erreur", f"Erreur au démarrage :\n{e}"))
            root.after(0, lambda: (btn_start.config(bg="#1B5E20"), btn_stop.config(bg=RED_BG)))

    import threading
    threading.Thread(target=_init_and_start, daemon=True).start()

def _do_stop():
    btn_start.config(bg="#1B5E20")
    btn_stop.config(bg=RED_BG)
    process.stop_all_sources()

def _on_start():
    _do_start()

def _on_stop():
    open_stop_auth_popup(_do_stop)

# ============================================================
#  CONSTRUCTION GUI
# ============================================================
btn_start = None
btn_stop  = None

def build_header():
    hdr = tk.Frame(root, bg=BG_HDR, pady=14)
    hdr.pack(fill="x")
    row = tk.Frame(hdr, bg=BG_HDR)
    row.pack()
    tk.Label(row, text=IC_BOLT, font=(MDL2, 20),
             bg=BG_HDR, fg="#FFD54F").pack(side="left")
    tk.Label(row, text="  EdgeFusion",
             font=("Arial", 20, "bold"), bg=BG_HDR, fg=TEXT).pack(side="left")
    tk.Label(hdr, text="FUSION IA GATEWAY",
             font=("Arial", 9, "bold"), bg=BG_HDR, fg=TEXT_ACC).pack()
    tk.Label(hdr, text="OPC UA to MQTT — Multi-Sources",
             font=("Arial", 8), bg=BG_HDR, fg=TEXT_DIM).pack()
    tk.Frame(hdr, bg=BORDER, height=1).pack(fill="x", pady=(10, 0))

def build_brokers_section(parent):
    global _brokers_frame
    wrap = tk.Frame(parent, bg=BG_SEC, padx=14, pady=4)
    wrap.pack(fill="x", padx=14, pady=4)
    _section_header(wrap, "BROKERS MQTT", IC_BROKER)

    btn_row = tk.Frame(wrap, bg=BG_SEC)
    btn_row.pack(fill="x", pady=(4, 0))
    _make_btn(btn_row, f"{IC_ADD}  Ajouter Broker",
              lambda: open_broker_config()).pack(side="right")

    _brokers_frame = tk.Frame(wrap, bg=BG_SEC)
    _brokers_frame.pack(fill="x", pady=4)
    update_brokers_list()

def build_sources_section(parent):
    global _sources_frame
    wrap = tk.Frame(parent, bg=BG_SEC, padx=14, pady=4)
    wrap.pack(fill="x", padx=14, pady=4)
    _section_header(wrap, "SOURCES OPC UA", IC_SOURCE)

    btn_row = tk.Frame(wrap, bg=BG_SEC)
    btn_row.pack(fill="x", pady=(4, 0))
    _make_btn(btn_row, f"{IC_ADD}  Ajouter Source",
              lambda: open_source_config()).pack(side="right")

    _sources_frame = tk.Frame(wrap, bg=BG_SEC)
    _sources_frame.pack(fill="x", pady=4)
    update_sources_list()

_journal_text    = None
_journal_only_bad = False

def build_journal_section(parent):
    global _journal_text, _journal_only_bad

    wrap = tk.Frame(parent, bg=BG_SEC, padx=14, pady=4)
    wrap.pack(fill="x", padx=14, pady=4)
    _section_header(wrap, "JOURNAL DES DONNÉES", "📋")

    # ---- barre de contrôle ----
    ctrl = tk.Frame(wrap, bg=BG_SEC)
    ctrl.pack(fill="x", pady=(4, 2))

    filter_var = tk.BooleanVar(value=False)

    def _toggle_filter():
        global _journal_only_bad
        _journal_only_bad = filter_var.get()
        _refresh_journal()

    tk.Checkbutton(
        ctrl, text="Afficher uniquement les anomalies",
        variable=filter_var, command=_toggle_filter,
        bg=BG_SEC, fg=TEXT_DIM, selectcolor=BG_ENTRY,
        activebackground=BG_SEC, font=("Arial", 8)
    ).pack(side="left")

    _make_btn(ctrl, "🗑  Effacer", lambda: [_journal.clear(), _refresh_journal()]).pack(side="right")

    # ---- en-tête colonnes ----
    hdr = tk.Frame(wrap, bg=BG_TITLE)
    hdr.pack(fill="x", pady=(4, 0))
    for col, w in [("Heure", 10), ("Source", 10), ("Tag", 20), ("Node ID", 28), ("Valeur", 10), ("Qualité", 9), ("Problème", 25)]:
        tk.Label(hdr, text=col, font=("Courier", 8, "bold"),
                 bg=BG_TITLE, fg=TEXT_ACC, width=w, anchor="w").pack(side="left", padx=2)

    # ---- zone texte scrollable ----
    txt_frame = tk.Frame(wrap, bg=BG_SEC)
    txt_frame.pack(fill="both", expand=True)

    vsb = tk.Scrollbar(txt_frame)
    vsb.pack(side="right", fill="y")
    hsb = tk.Scrollbar(txt_frame, orient="horizontal")
    hsb.pack(side="bottom", fill="x")

    _journal_text = tk.Text(
        txt_frame, height=10,
        bg="#060D1A", fg=TEXT,
        font=("Courier", 8),
        yscrollcommand=vsb.set,
        xscrollcommand=hsb.set,
        state="disabled", wrap="none",
        relief="flat", bd=0
    )
    _journal_text.pack(side="left", fill="both", expand=True)
    vsb.config(command=_journal_text.yview)
    hsb.config(command=_journal_text.xview)

    # Tags couleurs
    _journal_text.tag_configure("good",     foreground=GREEN)
    _journal_text.tag_configure("bad",      foreground=RED)
    _journal_text.tag_configure("recover",  foreground="#FFA726")
    _journal_text.tag_configure("dim",      foreground=TEXT_DIM)


def _refresh_journal():
    """Met à jour le widget texte avec les dernières entrées du journal."""
    if _journal_text is None:
        return
    entries = _journal.get_entries(only_bad=_journal_only_bad)

    _journal_text.config(state="normal")
    _journal_text.delete("1.0", "end")

    for e in reversed(entries):   # plus récent en haut
        heure   = e["ts"][11:] if len(e["ts"]) > 8 else e["ts"]
        source  = e["source"][:10].ljust(10)
        tag     = e["tag"][:20].ljust(20)
        node_id = e.get("node_id", "")[:28].ljust(28)
        value   = str(e["value"])[:10].ljust(10)
        reason  = e["reason"]

        if not e["ok"]:
            qualite = "MAUVAISE"
            tag_col = "bad"
        else:
            qualite = "BONNE   "
            tag_col = "good"

        line = f"{heure}  {source}  {tag}  {node_id}  {value}  {qualite}  {reason}\n"
        _journal_text.insert("end", line, tag_col)

    _journal_text.config(state="disabled")


def build_options_section(parent):
    cfg  = config_get_options()
    wrap = tk.Frame(parent, bg=BG_SEC, padx=14, pady=4)
    wrap.pack(fill="x", padx=14, pady=4)
    _section_header(wrap, "OPTIONS", IC_OPT)

    body = tk.Frame(wrap, bg=BG_SEC, padx=12, pady=8)
    body.pack(fill="x")
    body.columnconfigure(1, weight=1)

    e_refresh   = _make_field(body, 0, "Refresh (s)",   default=str(cfg.get("refresh",    2)))
    e_reconnect = _make_field(body, 1, "Reconnect (s)", default=str(cfg.get("reconnect",  5)))

    adv_frame = tk.Frame(body, bg=BG_SEC)
    adv_frame.columnconfigure(1, weight=1)
    e_buffer = _make_field(adv_frame, 0, "Buffer max", default=str(cfg.get("max_buffer", 1000)))

    def _toggle_adv():
        if adv_frame.winfo_ismapped():
            adv_frame.grid_remove()
            btn_adv.config(text="▶  Avancé")
        else:
            adv_frame.grid(row=3, column=0, columnspan=2, sticky="ew")
            btn_adv.config(text="▼  Avancé")

    btn_adv = tk.Button(body, text="▶  Avancé",
                        font=("Arial", 9), bg=BG_SEC, fg=TEXT_ACC,
                        relief="flat", cursor="hand2", command=_toggle_adv)
    btn_adv.grid(row=2, column=0, columnspan=2, sticky="w", pady=(4, 2))

    def _save_options():
        try:
            cfg_new = config_load()
            cfg_new["options"] = {
                "refresh":    float(e_refresh.get()),
                "reconnect":  float(e_reconnect.get()),
                "max_buffer": int(e_buffer.get())
            }
            config_save(cfg_new)
        except Exception as e:
            show_popup_error("Erreur Options", str(e))

    _make_btn(body, "💾  Sauvegarder", _save_options).grid(
        row=4, column=0, columnspan=2, sticky="ew", pady=(6, 0))

def build_buttons():
    global btn_start, btn_stop
    wrap = tk.Frame(root, bg=BG, padx=14)
    wrap.pack(fill="x", pady=8)
    wrap.columnconfigure(0, weight=1)
    wrap.columnconfigure(1, weight=1)

    btn_start = tk.Button(wrap, text="▶  START",
                          font=("Arial", 12, "bold"),
                          bg="#1B5E20", fg="#A5D6A7",
                          relief="flat", highlightthickness=1,
                          highlightbackground=GREEN_BD,
                          command=_on_start, cursor="hand2", pady=10)
    btn_start.grid(row=0, column=0, padx=(0, 6), sticky="ew")

    btn_stop = tk.Button(wrap, text="■  STOP",
                         font=("Arial", 12, "bold"),
                         bg=RED_BG, fg="#FFCDD2",
                         relief="flat", highlightthickness=1,
                         highlightbackground=RED_BD,
                         command=_on_stop, cursor="hand2", pady=10)
    btn_stop.grid(row=0, column=1, padx=(6, 0), sticky="ew")

def build_footer():
    tk.Frame(root, bg=BORDER, height=1).pack(fill="x")
    ftr = tk.Frame(root, bg=BG_HDR, pady=8)
    ftr.pack(fill="x")
    tk.Label(ftr, text="Edge Fusion  |  Multi-Sources Gateway",
             font=("Arial", 8), bg=BG_HDR, fg=TEXT_DIM).pack()
    tk.Label(ftr, text="© 2026 ManaTechnology",
             font=("Arial", 8, "bold"), bg=BG_HDR, fg=TEXT_ACC).pack()

def _apply_popup_icon(popup):
    """Applique l'icône app aux popups."""
    if _icon_path:
        try:
            popup.after(100, lambda: popup.iconbitmap(_icon_path))
        except Exception:
            pass

def _build_scrollable_area():
    """
    Crée la zone centrale scrollable.
    Structure : root → container → (canvas + scrollbar verticale)
                canvas → _content_frame  (toutes les sections ici)
    Défilement : molette souris + scrollbar.
    """
    global _content_frame

    container = tk.Frame(root, bg=BG)
    container.pack(fill="both", expand=True)

    # Scrollbar verticale (style sombre)
    vscroll = tk.Scrollbar(container, orient="vertical",
                           bg=BG_SEC, troughcolor=BG,
                           activebackground=TEXT_ACC,
                           highlightthickness=0, bd=0, width=10)
    vscroll.pack(side="right", fill="y")

    # Canvas
    canvas = tk.Canvas(container, bg=BG, highlightthickness=0,
                       yscrollcommand=vscroll.set, bd=0)
    canvas.pack(side="left", fill="both", expand=True)
    vscroll.config(command=canvas.yview)

    # Frame intérieure (contenu réel)
    _content_frame = tk.Frame(canvas, bg=BG)
    win_id = canvas.create_window((0, 0), window=_content_frame, anchor="nw")

    # Mise à jour scrollregion quand le contenu change de taille
    def _on_frame_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
    _content_frame.bind("<Configure>", _on_frame_configure)

    # Frame intérieure s'étire à la largeur du canvas
    def _on_canvas_configure(event):
        canvas.itemconfig(win_id, width=event.width)
    canvas.bind("<Configure>", _on_canvas_configure)

    # Molette souris → scroll
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    canvas.bind_all("<MouseWheel>", _on_mousewheel)


def build_gui(root_window, icon_path=None):
    """Construit toute la fenêtre principale."""
    global root, _icon_path
    root       = root_window
    _icon_path = icon_path
    root.configure(bg=BG)
    root.title("EdgeFusion")
    root.resizable(True, True)

    # ---- Zones fixes (haut) ----
    build_header()

    # ---- Zone centrale scrollable ----
    _build_scrollable_area()                    # crée _content_frame
    build_status_bar(_content_frame)
    build_brokers_section(_content_frame)
    build_sources_section(_content_frame)
    build_options_section(_content_frame)
    build_journal_section(_content_frame)

    # ---- Zones fixes (bas) ----
    build_buttons()
    build_footer()

    # Taille initiale : largeur min 520, hauteur = 70 % de l'écran (max 750)
    root.update_idletasks()
    screen_h = root.winfo_screenheight()
    w = max(520, root.winfo_reqwidth())
    h = min(int(screen_h * 0.70), 750)
    root.geometry(f"{w}x{h}")
    root.minsize(480, 400)

    # Fermer = authentification avant de minimiser dans le tray
    root.protocol("WM_DELETE_WINDOW", _on_close)

def _on_close():
    """Fermer la fenêtre = minimise dans le tray SANS authentification."""
    root.withdraw()


def open_quit_auth_popup():
    """Popup QUITTER — toujours affichée."""
    def _do_quit():
        import process
        process.stop_all_sources()
        root.destroy()

    _auth_popup(
        title      = "QUITTER L'APPLICATION",
        subtitle   = "Cette action arrêtera tous les bridges OPC→MQTT",
        btn_text   = "❌  Quitter",
        btn_bg     = RED_BG,
        btn_bd     = RED_BD,
        btn_fg     = RED,
        on_confirmed = _do_quit
    )
