import customtkinter as ctk

THEMES = {
    "Blue": {
        "primary":( "#2563EB", "#3B82F6"), 
        "hover": ("#1D4ED8", "#2563EB"),
        "sidebar": ("#1E293B", "#0F172A"),
        "card":    ("#FFFFFF", "#1E293B"),
        "text":    ("#0F172A", "#F1F5F9"), 
        "muted":   ("#64748B", "#94A3B8"), 
    },
    "Green": {
        "primary":( "#059669","#42BD96"),
        "hover": ("#059669","#42BD96" ),
        "sidebar":( "#052E2B", "#052E16"),
        "card":( "#FFFFFF", "#1E293B"),
        "text":("#0F172A","#FFFFFF",),
        "muted":( "#64748B", "#94A3B8"),
    },
    "Purple": {
        "primary":( "#7C3AED", "#885CDF"),
        "hover": ( "#5A14CA", "#885CDF"),
        "sidebar":(  "#052E2B", "#052E16"),
        "card":( "#FFFFFF", "#1E293B"),
        "text":("#0F172A","#FFFFFF",),
        "muted":( "#64748B", "#94A3B8"),
    },
}


def apply_appearance(mode):
    ctk.set_appearance_mode(mode)


def set_theme(name):
    return THEMES.get(name, THEMES["Blue"])
