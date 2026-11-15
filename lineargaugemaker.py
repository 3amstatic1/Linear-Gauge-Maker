import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageDraw, ImageFont, ImageTk, ImageColor
import json
import os

PRESETS_FILE = "gauge_presets.json"

def parse_color_sequence(seq_str, rel_pos):
    """Parses a Roblox-style color sequence (time: color; ...) and correctly interpolates RGB."""
    try:
        parts = [p.strip() for p in seq_str.split(";") if p.strip()]
        if not parts:
            return (100, 180, 220)
            
        keypoints = []
        for part in parts:
            if ":" in part:
                t_str, c_str = part.split(":", 1)
                t = float(t_str.strip())
                c_str = c_str.strip()
                if c_str.startswith("#") or c_str.isalpha():
                    rgb = ImageColor.getrgb(c_str)
                else:
                    rgb = tuple(int(x.strip()) for x in c_str.split(","))
                keypoints.append((t, rgb))
                
        if not keypoints:
            return (100, 180, 220)
            
        keypoints.sort(key=lambda x: x[0])
        
        if rel_pos <= keypoints[0][0]:
            return keypoints[0][1]
        if rel_pos >= keypoints[-1][0]:
            return keypoints[-1][1]
            
        for i in range(len(keypoints) - 1):
            t1, c1 = keypoints[i]
            t2, c2 = keypoints[i+1]
            if t1 <= rel_pos <= t2:
                factor = (rel_pos - t1) / (t2 - t1) if t2 > t1 else 0
                r = int(c1[0] + (c2[0] - c1[0]) * factor)
                g = int(c1[1] + (c2[1] - c1[1]) * factor)
                b = int(c1[2] + (c2[2] - c1[2]) * factor)
                return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
                
        return keypoints[0][1]
    except Exception:
        return (100, 180, 220)


def evaluate_transparency_sequence(seq_str, rel_pos):
    """Parses Roblox-style transparency sequence (time, transparency; ...) -> Alpha (0-255)."""
    try:
        pairs = []
        for part in seq_str.split(";"):
            if "," in part:
                t, val = part.split(",")
                pairs.append((float(t.strip()), float(val.strip())))
        
        if not pairs:
            return 255
            
        pairs.sort(key=lambda x: x[0])
        
        if rel_pos <= pairs[0][0]:
            transparency = pairs[0][1]
        elif rel_pos >= pairs[-1][0]:
            transparency = pairs[-1][1]
        else:
            transparency = pairs[0][1]
            for i in range(len(pairs) - 1):
                t1, v1 = pairs[i]
                t2, v2 = pairs[i+1]
                if t1 <= rel_pos <= t2:
                    factor = (rel_pos - t1) / (t2 - t1) if t2 > t1 else 0
                    transparency = v1 + (v2 - v1) * factor
                    break
                    
        return int((1.0 - max(0.0, min(1.0, transparency))) * 255)
    except Exception:
        return 255


def generate_gauge_image(
    width=900,
    height=450,
    min_val=-60.0,
    max_val=60.0,
    current_val=-60.0,
    title="Cooling Tower Level Change",
    unit="[cm/min]",
    major_step=12.0,
    minor_divisions=5,
    face_color=(235, 248, 235),
    needle_color=(20, 20, 35),
    zones_config="-12, 12",
    color_seq="0: #64B4DC; 0.5: #FFFFFF; 1: #64B4DC",
    transparency_seq="0, 0; 0.5, 1; 1, 0",
    use_gradient=True,
    zone_y_offset=0,
    zone_height=24,
    title_y_offset=0,
    unit_y_offset=0,
    highlight_center=True,
    center_line_color=(0, 120, 255, 255),
    show_needle=True,
    font_path=""
):
    # Ensure face color is a full RGBA 4-tuple with solid alpha (255)
    if isinstance(face_color, (list, tuple)):
        bg_rgba = tuple(face_color[:3]) + (255,) if len(face_color) >= 3 else (235, 248, 235, 255)
    else:
        bg_rgba = (235, 248, 235, 255)

    # 1. Create base image with solid RGBA background
    img = Image.new("RGBA", (width, height), bg_rgba)
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([0, 0, width - 1, height - 1], outline=(150, 150, 150, 255), width=1)
    
    # 2. Scale layout coordinates
    scale_y = height * 0.42
    scale_x_start = int(width * 0.12)
    scale_x_end = width - int(width * 0.12)
    scale_width = scale_x_end - scale_x_start
    
    def val_to_x(val):
        fraction = (val - min_val) / (max_val - min_val)
        return scale_x_start + fraction * scale_width

    # Fonts
    try:
        if font_path:
            font_large = ImageFont.truetype(font_path, int(height * 0.04))
            font_small = ImageFont.truetype(font_path, int(height * 0.033))
        else:
            font_large = ImageFont.truetype("arial.ttf", int(height * 0.04))
            font_small = ImageFont.truetype("arial.ttf", int(height * 0.033))
    except IOError:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # 3. Parse and Draw Zones with Accurate Gradient Mapping
    half_h = zone_height // 2
    zone_top = int(scale_y + zone_y_offset - half_h)
    zone_bottom = int(scale_y + zone_y_offset + half_h)

    if zones_config.strip():
        zone_entries = zones_config.split(";")
        for entry in zone_entries:
            parts = [p.strip() for p in entry.split(",")]
            if len(parts) >= 2:
                try:
                    z_min = float(parts[0])
                    z_max = float(parts[1])

                    z_start_x = int(val_to_x(z_min))
                    z_end_x = int(val_to_x(z_max))
                    z_w = max(1, z_end_x - z_start_x)

                    for x_pos in range(z_start_x, z_end_x):
                        # Calculate accurate relative position (0.0 to 1.0) across the zone span
                        rel_pos = (x_pos - z_start_x) / z_w if use_gradient else 0.0
                        
                        rgb = parse_color_sequence(color_seq, rel_pos)
                        alpha = evaluate_transparency_sequence(transparency_seq, rel_pos)

                        # Draw pixel vertical slice with proper RGBA color/alpha blending
                        for y_pos in range(zone_top, zone_bottom + 1):
                            # Alpha composite blending over background if transparency is active
                            if alpha < 255:
                                bg_pixel = img.getpixel((x_pos, y_pos))
                                a_factor = alpha / 255.0
                                inv_a = 1.0 - a_factor
                                blended_r = int(rgb[0] * a_factor + bg_pixel[0] * inv_a)
                                blended_g = int(rgb[1] * a_factor + bg_pixel[1] * inv_a)
                                blended_b = int(rgb[2] * a_factor + bg_pixel[2] * inv_a)
                                img.putpixel((x_pos, y_pos), (blended_r, blended_g, blended_b, 255))
                            else:
                                img.putpixel((x_pos, y_pos), (rgb[0], rgb[1], rgb[2], 255))
                except Exception:
                    pass

    # Re-initialize draw context after manual putpixel modifications
    draw = ImageDraw.Draw(img)

    # Main horizontal baseline
    draw.line([(scale_x_start, scale_y), (scale_x_end, scale_y)], fill=(0, 0, 0, 255), width=2)

    # 4. Ticks, Centered Labels, and Center Line Highlight
    center_val = (min_val + max_val) / 2.0
    total_range = max_val - min_val
    if total_range > 0:
        num_major_steps = int(total_range / major_step)
        for i in range(num_major_steps + 1):
            v = min_val + i * major_step
            x = val_to_x(v)
            
            is_center_line = highlight_center and abs(v - center_val) < 1e-5
            line_col = center_line_color if isinstance(center_line_color, tuple) else (0, 120, 255, 255)
            if len(line_col) == 3:
                line_col = line_col + (255,)
            
            line_col_final = line_col if is_center_line else (0, 0, 0, 255)
            line_width = 3 if is_center_line else 2
            
            draw.line([(x, scale_y), (x, scale_y - int(height * 0.084))], fill=line_col_final, width=line_width)
            
            label = f"{int(v)}" if v.is_integer() else f"{v}"
            bbox = font_large.getbbox(label)
            text_width = bbox[2] - bbox[0]
            draw.text((x - text_width / 2, scale_y - int(height * 0.14)), label, fill=(0, 0, 0, 255), font=font_large)
            
            if i < num_major_steps:
                minor_step_val = major_step / minor_divisions
                for m in range(1, minor_divisions):
                    mv = v + m * minor_step_val
                    if mv <= max_val:
                        mx = val_to_x(mv)
                        draw.line([(mx, scale_y), (mx, scale_y - int(height * 0.044))], fill=(0, 0, 0, 255), width=1)

    # 5. Title and Unit with Adjustable Offsets
    title_y = (height * 0.65) + title_y_offset
    unit_y = (height * 0.77) + unit_y_offset
    
    t_bbox = font_small.getbbox(title)
    u_bbox = font_small.getbbox(unit)
    draw.text((width / 2 - (t_bbox[2] - t_bbox[0]) / 2, title_y), title, fill=(0, 0, 0, 255), font=font_small)
    draw.text((width / 2 - (u_bbox[2] - u_bbox[0]) / 2, unit_y), unit, fill=(0, 0, 0, 255), font=font_small)

    # 6. Optional Needle Pointer
    if show_needle:
        needle_x = val_to_x(current_val)
        needle_polygon = [
            (needle_x - 5, scale_y + int(height * 0.1)),
            (needle_x + 5, scale_y + int(height * 0.1)),
            (needle_x, scale_y - 4)
        ]
        n_col = needle_color if isinstance(needle_color, tuple) else (20, 20, 35, 255)
        if len(n_col) == 3:
            n_col = n_col + (255,)
        draw.polygon(needle_polygon, fill=n_col)

    return img


class GaugeMakerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Linear Gauge Maker")
        self.root.geometry("1150x1160")

        control_frame = ttk.LabelFrame(root, text=" Gauge Parameters & Presets ", padding=12)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        preview_frame = ttk.LabelFrame(root, text=" Live Preview ", padding=10)
        preview_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Preset Management Toolbar ---
        preset_toolbar = ttk.Frame(control_frame)
        preset_toolbar.grid(row=0, column=0, columnspan=4, sticky=tk.W, pady=(0, 10))

        ttk.Label(preset_toolbar, text="Preset:").pack(side=tk.LEFT, padx=(0, 5))
        self.preset_combo = ttk.Combobox(preset_toolbar, width=25, state="readonly")
        self.preset_combo.pack(side=tk.LEFT, padx=(0, 5))
        self.preset_combo.bind("<<ComboboxSelected>>", self.load_preset)

        btn_save_preset = ttk.Button(preset_toolbar, text="Save Preset", command=self.save_preset)
        btn_save_preset.pack(side=tk.LEFT, padx=(0, 5))

        btn_delete_preset = ttk.Button(preset_toolbar, text="Delete Preset", command=self.delete_preset)
        btn_delete_preset.pack(side=tk.LEFT)

        self.entries = {}

        fields = [
            ("Default Filename:", "linear_gauge.png", "filename"),
            ("Width:", "900", "width"),
            ("Height:", "450", "height"),
            ("Title:", "Cooling Tower Level Change", "title"),
            ("Units:", "[cm/min]", "units"),
            ("Min Value:", "-60.0", "min"),
            ("Max Value:", "60.0", "max"),
            ("Current Value:", "-60.0", "current"),
            ("Major Step:", "12.0", "major"),
            ("Face Color:", "#EBF8EB", "face"),
            ("Needle Color:", "#141423", "needle"),
            ("Color Sequence:", "0: #64B4DC; 0.5: #FFFFFF; 1: #64B4DC", "color_seq"),
            ("Transparency Sequence:", "0, 0; 0.5, 1; 1, 0", "trans_seq"),
            ("Zone Y-Offset:", "0", "z_offset"),
            ("Zone Height:", "24", "z_height"),
            ("Title Y-Offset:", "0", "title_offset"),
            ("Unit Y-Offset:", "0", "unit_offset"),
            ("Center Line Color:", "#0078FF", "center_color"),
            ("Zones Ranges (min,max; ...):", "-12, 12", "zones")
        ]

        for idx, (label_text, default_val, key_name) in enumerate(fields):
            row = (idx // 2) + 1
            col = (idx % 2) * 2

            lbl = ttk.Label(control_frame, text=label_text)
            lbl.grid(row=row, column=col, sticky=tk.W, padx=5, pady=3)

            var = tk.StringVar(value=default_val)
            if key_name != "filename":
                var.trace_add("write", lambda *args: self.update_preview())
            
            entry = ttk.Entry(control_frame, textvariable=var, width=32 if "Sequence" in label_text or key_name=="zones" else 22)
            entry.grid(row=row, column=col+1, sticky=tk.W, padx=5, pady=3)
            
            self.entries[key_name] = var

        opt_row = (len(fields) // 2) + 2
        
        self.show_needle_var = tk.BooleanVar(value=True)
        self.show_needle_var.trace_add("write", lambda *args: self.update_preview())
        ttk.Checkbutton(control_frame, text="Show Needle", variable=self.show_needle_var).grid(row=opt_row, column=0, sticky=tk.W, padx=5, pady=6)

        self.use_gradient_var = tk.BooleanVar(value=True)
        self.use_gradient_var.trace_add("write", lambda *args: self.update_preview())
        ttk.Checkbutton(control_frame, text="Use Color/Transparency Gradient", variable=self.use_gradient_var).grid(row=opt_row, column=1, sticky=tk.W, padx=5, pady=6)

        self.highlight_center_var = tk.BooleanVar(value=True)
        self.highlight_center_var.trace_add("write", lambda *args: self.update_preview())
        ttk.Checkbutton(control_frame, text="Highlight Center Line", variable=self.highlight_center_var).grid(row=opt_row, column=2, sticky=tk.W, padx=5, pady=6)

        # Font path selector
        ttk.Label(control_frame, text="Custom Font (.ttf):").grid(row=opt_row+1, column=0, sticky=tk.W, padx=5, pady=6)
        
        font_frame = ttk.Frame(control_frame)
        font_frame.grid(row=opt_row+1, column=1, sticky=tk.W, padx=5, pady=6)
        
        self.font_var = tk.StringVar(value="")
        self.font_var.trace_add("write", lambda *args: self.update_preview())
        
        self.font_entry = ttk.Entry(font_frame, textvariable=self.font_var, width=15)
        self.font_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        btn_browse = ttk.Button(font_frame, text="Browse", width=7, command=self.browse_font)
        btn_browse.pack(side=tk.LEFT)

        # SAVE BUTTON
        btn_save = ttk.Button(control_frame, text="Save Gauge File As...", command=self.save_gauge_file)
        btn_save.grid(row=opt_row + 2, column=0, columnspan=4, pady=12)

        self.preview_label = ttk.Label(preview_frame)
        self.preview_label.pack(fill=tk.BOTH, expand=True)

        self.refresh_presets_list()
        self.update_preview()

    def browse_font(self):
        filename = filedialog.askopenfilename(filetypes=[("TrueType Fonts", "*.ttf"), ("All Files", "*.*")])
        if filename:
            self.font_var.set(filename)

    def get_current_params(self):
        return {
            "filename": self.entries["filename"].get(),
            "width": int(self.entries["width"].get()),
            "height": int(self.entries["height"].get()),
            "title": self.entries["title"].get(),
            "unit": self.entries["units"].get(),
            "min_val": float(self.entries["min"].get()),
            "max_val": float(self.entries["max"].get()),
            "current_val": float(self.entries["current"].get()),
            "major_step": float(self.entries["major"].get()),
            "face_color": ImageColor.getrgb(self.entries["face"].get()),
            "needle_color": ImageColor.getrgb(self.entries["needle"].get()),
            "zones_config": self.entries["zones"].get(),
            "color_seq": self.entries["color_seq"].get(),
            "transparency_seq": self.entries["trans_seq"].get(),
            "z_offset": int(self.entries["z_offset"].get()),
            "z_height": int(self.entries["z_height"].get()),
            "title_offset": int(self.entries["title_offset"].get()),
            "unit_offset": int(self.entries["unit_offset"].get()),
            "center_color": ImageColor.getrgb(self.entries["center_color"].get()),
            "show_needle": self.show_needle_var.get(),
            "use_gradient": self.use_gradient_var.get(),
            "highlight_center": self.highlight_center_var.get(),
            "font_path": self.font_var.get().strip()
        }

    def update_preview(self):
        try:
            p = self.get_current_params()
            img = generate_gauge_image(
                width=p["width"], height=p["height"], min_val=p["min_val"], max_val=p["max_val"],
                current_val=p["current_val"], title=p["title"], unit=p["unit"], major_step=p["major_step"],
                face_color=p["face_color"], needle_color=p["needle_color"], zones_config=p["zones_config"],
                color_seq=p["color_seq"], transparency_seq=p["transparency_seq"], use_gradient=p["use_gradient"],
                zone_y_offset=p["z_offset"], zone_height=p["z_height"], title_y_offset=p["title_offset"],
                unit_y_offset=p["unit_offset"], highlight_center=p["highlight_center"], center_line_color=p["center_color"],
                show_needle=p["show_needle"], font_path=p["font_path"]
            )
            preview_img = img.resize((750, 350), Image.Resampling.LANCZOS)
            self.tk_img = ImageTk.PhotoImage(preview_img)
            self.preview_label.config(image=self.tk_img)
        except Exception:
            pass 

    def save_gauge_file(self):
        try:
            default_name = self.entries["filename"].get()
            filepath = filedialog.asksaveasfilename(
                defaultextension=".png",
                initialfile=default_name,
                filetypes=[("PNG Image", "*.png"), ("All Files", "*.*")]
            )
            if not filepath:
                return

            p = self.get_current_params()
            img = generate_gauge_image(
                width=p["width"], height=p["height"], min_val=p["min_val"], max_val=p["max_val"],
                current_val=p["current_val"], title=p["title"], unit=p["unit"], major_step=p["major_step"],
                face_color=p["face_color"], needle_color=p["needle_color"], zones_config=p["zones_config"],
                color_seq=p["color_seq"], transparency_seq=p["transparency_seq"], use_gradient=p["use_gradient"],
                zone_y_offset=p["z_offset"], zone_height=p["z_height"], title_y_offset=p["title_offset"],
                unit_y_offset=p["unit_offset"], highlight_center=p["highlight_center"], center_line_color=p["center_color"],
                show_needle=p["show_needle"], font_path=p["font_path"]
            )
            # Convert to RGB before saving standard PNG if full alpha channels aren't needed, 
            # or keep RGBA so transparency works properly.
            img_to_save = img.convert("RGB") if "transparency_seq" not in p else img
            img_to_save.save(filepath)
            messagebox.showinfo("Success", f"Gauge image successfully saved to:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save image:\n{e}")

    def load_presets_data(self):
        if os.path.exists(PRESETS_FILE):
            try:
                with open(PRESETS_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def refresh_presets_list(self):
        data = self.load_presets_data()
        presets = list(data.keys())
        self.preset_combo['values'] = presets
        if presets:
            self.preset_combo.set(presets[0])

    def save_preset(self):
        preset_name = self.preset_combo.get().strip()
        if not preset_name:
            preset_name = "Default Preset"

        dialog = tk.Toplevel(self.root)
        dialog.title("Save Preset")
        dialog.geometry("300x120")
        
        ttk.Label(dialog, text="Enter Preset Name:").pack(padx=10, pady=(10, 5))
        name_var = tk.StringVar(value=preset_name)
        entry_name = ttk.Entry(dialog, textvariable=name_var, width=30)
        entry_name.pack(padx=10, pady=5)

        def confirm_save():
            name = name_var.get().strip()
            if name:
                data = self.load_presets_data()
                preset_data = {k: v.get() for k, v in self.entries.items()}
                preset_data["show_needle"] = self.show_needle_var.get()
                preset_data["use_gradient"] = self.use_gradient_var.get()
                preset_data["highlight_center"] = self.highlight_center_var.get()
                preset_data["font_path"] = self.font_var.get()

                data[name] = preset_data
                with open(PRESETS_FILE, "w") as f:
                    json.dump(data, f, indent=4)

                self.refresh_presets_list()
                self.preset_combo.set(name)
                dialog.destroy()
                messagebox.showinfo("Preset Saved", f"Preset '{name}' saved successfully!")

        ttk.Button(dialog, text="Save", command=confirm_save).pack(pady=5)

    def load_preset(self, event=None):
        name = self.preset_combo.get()
        data = self.load_presets_data()
        if name in data:
            p_data = data[name]
            for k, var in self.entries.items():
                if k in p_data:
                    var.set(p_data[k])
            if "show_needle" in p_data:
                self.show_needle_var.set(p_data["show_needle"])
            if "use_gradient" in p_data:
                self.use_gradient_var.set(p_data["use_gradient"])
            if "highlight_center" in p_data:
                self.highlight_center_var.set(p_data["highlight_center"])
            if "font_path" in p_data:
                self.font_var.set(p_data["font_path"])
            self.update_preview()

    def delete_preset(self):
        name = self.preset_combo.get()
        data = self.load_presets_data()
        if name in data:
            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete preset '{name}'?"):
                del data[name]
                with open(PRESETS_FILE, "w") as f:
                    json.dump(data, f, indent=4)
                self.refresh_presets_list()
                messagebox.showinfo("Deleted", f"Preset '{name}' deleted.")

if __name__ == "__main__":
    root = tk.Tk()
    app = GaugeMakerApp(root)
    root.mainloop()
