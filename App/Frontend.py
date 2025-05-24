import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, ttk
from tkinter import simpledialog, filedialog
from back import *
from back import BASE_DIR, FOTOS_PERFIL_DIR
from PIL import Image, ImageTk
import os 
import shutil
import uuid
import traceback
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

db=Database("basedatos")


def inicio_empleador(master, usuario= None): 
    ventana=ctk.CTkToplevel(master)
    ventana.title(f"Panel Empleador - {usuario['nombre']}" if usuario else "Inicio sesión - Empleador")
    ventana.geometry("950x750") 
    ventana.configure(fg_color="#9EC6F3")

    from back import BASE_DIR, FOTOS_PERFIL_DIR, DEFAULT_PROFILE_PIC

    ventana.grid_columnconfigure(0, weight=0)
    ventana.grid_columnconfigure(1, weight=1)
    ventana.grid_rowconfigure(0, weight=1)

    sidebar = tk.Frame(ventana, bg="#6fa4e1", width=300)
    sidebar.grid(row=0, column=0,  sticky="nsew")
    sidebar.grid_propagate(False)
    sidebar.pack_propagate(False)

    
    nombre_foto = usuario.get("foto", "").strip() if usuario else ""

    if nombre_foto:
        ruta_foto_completa=os.path.join(FOTOS_PERFIL_DIR, nombre_foto)
    else:
        ruta_foto_completa = DEFAULT_PROFILE_PIC   
       
    try:
        if os.path.exists(ruta_foto_completa):
            img = Image.open(ruta_foto_completa)
            
        else:
            raise FileNotFoundError(f"No se encontró el archivo: {ruta_foto_completa}")
            
        img = img.resize((80, 80))
        photo = ImageTk.PhotoImage(img)
        
    except Exception as e:
        
        
        try:
            img = Image.open(DEFAULT_PROFILE_PIC).resize((80, 80))
            photo = ImageTk.PhotoImage(img)
            
        except:
            img = Image.new('RGB', (80, 80), color='#CCCCCC')
            photo = ImageTk.PhotoImage(img)
            
    
    
    icono_usuario = tk.Label(sidebar, image=photo, bg="#6fa4e1")
    icono_usuario.image = photo  
    icono_usuario.pack(pady=(20, 10), anchor="nw", padx=10)

    nombre_usuario= usuario['nombre'] if usuario else "Empleador"
    tk.Label(sidebar, text= nombre_usuario, bg= "#6fa4e1", fg="white", font=("Open Sans", 20, "bold")).pack(anchor="nw", padx=10, pady=(0,20))
    
    def eliminar_cuenta():
        if not usuario or 'ID' not in usuario:
            messagebox.showerror("Error", "Datos de usuario incompletos", parent=ventana)
            return

        if not messagebox.askyesno(
            "Confirmar eliminación",
            "¿Estás seguro de eliminar tu cuenta permanentemente?",
            icon='warning',
            parent=ventana
        ):
            return

        contraseña_ingresada = simpledialog.askstring(
            "Verificación",
            "Ingresa tu contraseña actual para confirmar:",
            parent=ventana,
            show='*'
        )

        if not contraseña_ingresada:
            return

        usuario_en_db = next((u for u in db.data['usuarios'] if u['ID'] == usuario['ID']), None)

        if not usuario_en_db or str(contraseña_ingresada) != str(usuario_en_db['contraseña']):
            messagebox.showerror("Error", "Contraseña incorrecta", parent=ventana)
            return

        
        u = Usuario(
            ID=usuario['ID'],
            nombre=usuario['nombre'],
            contacto=usuario['contacto'],
            contraseña=usuario['contraseña'],
            tipo=usuario['tipo'],
            foto=usuario.get('foto', '')
        )

        if u.eliminar_cuenta(db):
            messagebox.showinfo("Éxito", "Cuenta eliminada correctamente", parent=ventana)
            ventana.destroy()
            master.deiconify()
        else:
            messagebox.showerror("Error", "No se pudo eliminar la cuenta", parent=ventana)
        db.data = db._load_data()

    def editar_cuenta():
        if not usuario or 'ID' not in usuario or 'tipo' not in usuario:
            messagebox.showerror("Error", "Datos de usuario incompletos", parent=ventana)
            return
        
        user_id = usuario['ID']
        user_type = usuario['tipo']
        
        user_data = db.get_user_by_id(user_id) or {}
        empleador_data = db.get_empleador_by_id(user_id) if user_type == 'empleador' else {}
        
        if not user_data:
            messagebox.showerror("Error", "Usuario no encontrado", parent=ventana)
            return

        ventana.withdraw()
        ventanaec = ctk.CTkToplevel()
        ventanaec.title(f"Editar información - {usuario.get('nombre', '')}")
        ventanaec.geometry("800x650")
        ventanaec.configure(fg_color="#BDDDE4")

        
        ventanaec.grid_columnconfigure(0, weight=1)
        ventanaec.grid_columnconfigure(1, weight=2)
        ventanaec.grid_columnconfigure(2, weight=1)

        
        titulo = ctk.CTkLabel(ventanaec,
                            text="Editar información",
                            font=("Open Sans", 30, "bold"),
                            text_color="white")
        titulo.grid(row=0, column=0, columnspan=3, pady=(30, 20))

        
        def seleccionar_imagen():
            ruta = filedialog.askopenfilename(
                title="Seleccionar imagen",
                filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg")]
            )
            if ruta:
                entries["foto"].delete(0, tk.END)
                entries["foto"].insert(0, ruta)

        
        campos = [
            {"label": "Nombre:", "key": "nombre", "row": 1, "source": "user"},
            {"label": "Contacto:", "key": "contacto", "row": 2, "source": "user"},
            {"label": "Método de pago:", "key": "metodo_pago", "row": 3, "source": "empleador"},
            {"label": "Contraseña actual:", "key": "", "row": 4, "password": True},
            {"label": "Nueva contraseña:", "key": "", "row": 5, "password": True},
            {"label": "Foto de perfil:", "key": "foto", "row": 6, "source": "user"}
        ]

        if user_type == 'empleador':
            campos.extend([
                {"label": "Nivel:", "key": "nivel", "row": 7, "source": "empleador", "editable": False},
                {"label": "Reputación:", "key": "reputacion", "row": 8, "source": "empleador", "editable": False}
            ])
        else:
            campos.extend([
                {"label": "Profesión:", "key": "profesion", "row": 7, "source": "trabajador"},
                {"label": "Experiencia:", "key": "experiencia_lab", "row": 8, "source": "trabajador"}
            ])

        entries = {}

        for campo in campos:
           
            row_frame = ctk.CTkFrame(ventanaec, fg_color="transparent")
            row_frame.grid(row=campo["row"], column=0, columnspan=3, sticky="nsew", pady=5)
            row_frame.grid_columnconfigure(1, weight=1)

            
            lbl = ctk.CTkLabel(row_frame,
                            text=campo["label"],
                            font=("Open Sans", 18, "bold"),
                            anchor="e",
                            width=180)
            lbl.grid(row=0, column=0, padx=(50, 10), sticky="e")

           
            if campo.get("editable", True):
                entry = ctk.CTkEntry(row_frame,
                                    width=350,
                                    font=("Open Sans", 16),
                                    corner_radius=8)
                
                if campo.get("password"):
                    entry.configure(show="•")
                
                
                value = ""
                if campo.get("source") == "user":
                    value = user_data.get(campo["key"], "")
                elif campo.get("source") == "empleador":
                    value = empleador_data.get(campo["key"], "")
                
                if value:
                    entry.insert(0, str(value))
                
                entry.grid(row=0, column=1, sticky="ew", padx=(0, 20))
                entries[campo["key"] or campo["label"].lower()] = entry

                
                if campo["key"] == "foto":
                    btn_examinar = ctk.CTkButton(row_frame,
                                                text="Examinar",
                                                width=100,
                                                command=seleccionar_imagen)
                    btn_examinar.grid(row=0, column=2, padx=(0, 50))
            else:
                
                value = ""
                if campo["source"] == "empleador":
                    value = empleador_data.get(campo["key"], "")
                
                lbl_valor = ctk.CTkLabel(row_frame,
                                    text=str(value),
                                    font=("Open Sans", 16),
                                    anchor="w",
                                    width=350)
                lbl_valor.grid(row=0, column=1, sticky="w")

        
        def guardar_cambios():
            user_updates = {}
            empleador_updates = {}
            
            for campo in campos:
                if not campo.get("editable", True):
                    continue
                    
                key = campo["key"]
                entry = entries.get(key or campo["label"].lower())
                if entry:
                    value = str(entry.get()) if entry.get() else ""
                    
                    if campo.get("source") == "user":
                        user_updates[key] = value
                    elif campo.get("source") == "empleador":
                        empleador_updates[key] = value
            
            
            nueva_contraseña = entries.get("nueva contraseña:", "").get()
            if nueva_contraseña:
                contraseña_actual = entries.get("contraseña actual:", "").get()
                if str(contraseña_actual) != str(user_data.get("contraseña", "")):
                    messagebox.showerror("Error", "Contraseña actual incorrecta", parent=ventanaec)
                    return
                user_updates["contraseña"] = nueva_contraseña
            
            
            success = db.update_user(user_id, user_updates)
            if user_type == 'empleador':
                success &= db.update_empleador(user_id, empleador_updates)
            
            if success:
                messagebox.showinfo("Éxito", "Cambios guardados correctamente", parent=ventanaec)
                ventanaec.destroy()
                ventana.deiconify()
            else:
                messagebox.showerror("Error", "No se pudieron guardar los cambios", parent=ventanaec)

        
        btn_frame = ctk.CTkFrame(ventanaec, fg_color="transparent")
        btn_frame.grid(row=9, column=0, columnspan=3, pady=20)

        btn_aceptar = ctk.CTkButton(btn_frame,
                                text="Aceptar",
                                width=120,
                                height=40,
                                fg_color="#FFF1D5",
                                text_color="black",
                                font=("Open Sans", 15, "bold"),
                                command=guardar_cambios)
        btn_aceptar.pack(side="left", padx=20)

        btn_cancelar = ctk.CTkButton(btn_frame,
                                    text="Cancelar",
                                    width=120,
                                    height=40,
                                    fg_color="#FFF1D5",
                                    text_color="black",
                                    font=("Open Sans", 15, "bold"),
                                    command=lambda: [ventanaec.destroy(), ventana.deiconify()])
        btn_cancelar.pack(side="right", padx=20)

        ventanaec.protocol("WM_DELETE_WINDOW", lambda: [ventanaec.destroy(), ventana.deiconify()])

    btn_eliminar= ctk.CTkButton(sidebar, text="Eliminar perfil", font=("Open Sans",15, "bold"),fg_color="#FF6B6B", text_color="white", width=200, height=40, command= eliminar_cuenta)
    btn_eliminar.pack(side= "bottom", pady=30)

    btn_EDITAR= ctk.CTkButton(sidebar, text="Editar perfil", font=("Open Sans",15, "bold"),fg_color="#FFF1D5", text_color="black", width=200, height=40, command=editar_cuenta)
    btn_EDITAR.pack(pady=(0,10))

    main_frame = ctk.CTkFrame(ventana, fg_color="#9EC6F3")
    main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
    main_frame.grid_columnconfigure(0, weight=1)
    main_frame.grid_rowconfigure(1, weight=1)  
    main_frame.grid_rowconfigure(2, weight=1) 

    
    search_frame = ctk.CTkFrame(main_frame, fg_color="#9EC6F3")
    search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
    search_frame.grid_columnconfigure(1, weight=1)

    ctk.CTkLabel(search_frame, text="Buscar trabajadores:", font=("Open Sans", 16, "bold")).grid(row=0, column=0, padx=(0, 10))

    search_entry = ctk.CTkEntry(search_frame, width=300, font=("Open Sans", 14), placeholder_text="Ej: Fontanero, Electricista...")
    search_entry.grid(row=0, column=1, padx=(0, 10))

    def buscar_trabajadores():
        profesion = search_entry.get().strip().lower()
        if not profesion:
            messagebox.showwarning("Advertencia", "Por favor ingresa una profesión para buscar", parent=ventana)
            return
        
        try:
           
            trabajadores = []
            for trabajador_data in db.data['trabajadores']:
                
                usuario_data = db.get_user_by_id(trabajador_data['ID'])
                if usuario_data:
                    
                    trabajador_completo = {**usuario_data, **trabajador_data}
                    
                  
                    curriculum = next((cv for cv in db.data.get('curriculums', []) 
                                     if cv['ID_trabajador'] == trabajador_data['ID']), None)
                    if curriculum:
                        trabajador_completo.update(curriculum)
                    
                    trabajadores.append(trabajador_completo)
            
           
            resultados = [t for t in trabajadores 
                         if profesion in t.get('profesion', '').lower()]
            
           
            mostrar_resultados(resultados)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los trabajadores: {str(e)}", parent=ventana)

    search_button = ctk.CTkButton(search_frame, text="Buscar", font=("Open Sans", 14), command=buscar_trabajadores)
    search_button.grid(row=0, column=2)

    
    resultados_frame = ctk.CTkFrame(main_frame, fg_color="#FFFFFF")
    resultados_frame.grid(row=1, column=0, sticky="nsew")
    resultados_frame.grid_columnconfigure(0, weight=1)
    resultados_frame.grid_rowconfigure(0, weight=1)

   
    canvas = tk.Canvas(resultados_frame, bg="white", highlightthickness=0)
    scrollbar = ctk.CTkScrollbar(resultados_frame, orientation="vertical", command=canvas.yview)
    scrollable_frame = ctk.CTkFrame(canvas, fg_color="white")

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")

    notificaciones_frame = ctk.CTkFrame(main_frame, fg_color="#F1F8FF")
    notificaciones_frame.grid(row=2, column=0, sticky="nsew", pady=(10, 0))
    notificaciones_frame.grid_columnconfigure(0, weight=1)

    contenedor_notificaciones = ctk.CTkFrame(notificaciones_frame, fg_color="#FFFFFF")
    contenedor_notificaciones.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)


    for notif in db.obtener_notificaciones_empleador(usuario['ID']):
        mostrar_notificacion_individual_empleador(notificaciones_frame, notif, db, usuario)

    def mostrar_resultados(trabajadores):
        
        for widget in scrollable_frame.winfo_children():
            widget.destroy()
        
        if not trabajadores:
            ctk.CTkLabel(scrollable_frame, 
                         text="No se encontraron trabajadores con esa profesión",
                         font=("Open Sans", 16)).pack(pady=50)
            return
        
        for i, trabajador in enumerate(trabajadores):
           
            trabajador_frame = ctk.CTkFrame(scrollable_frame, fg_color="#E6F2FF", corner_radius=10)
            trabajador_frame.pack(fill="x", pady=5, padx=5)
            
            
            foto_path = os.path.join(FOTOS_PERFIL_DIR, trabajador.get('foto', ''))
            if not os.path.exists(foto_path):
                foto_path = DEFAULT_PROFILE_PIC
            
            try:
                img = Image.open(foto_path).resize((60, 60))
                photo = ImageTk.PhotoImage(img)
                foto_label = tk.Label(trabajador_frame, image=photo, bg="#E6F2FF")
                foto_label.image = photo
                foto_label.grid(row=0, column=0, rowspan=3, padx=10, pady=10, sticky="nw")
            except:
                pass
            
           
            ctk.CTkLabel(trabajador_frame, 
                         text=f"Nombre: {trabajador.get('nombre', '')}",
                         font=("Open Sans", 14, "bold")).grid(row=0, column=1, sticky="w", padx=5)
            
            ctk.CTkLabel(trabajador_frame, 
                         text=f"Profesión: {trabajador.get('profesion', '')}",
                         font=("Open Sans", 12)).grid(row=1, column=1, sticky="w", padx=5)
            
            ctk.CTkLabel(trabajador_frame, 
                         text=f"Experiencia: {trabajador.get('experiencia_lab', '')}",
                         font=("Open Sans", 12)).grid(row=2, column=1, sticky="w", padx=5)
            
           
            def ver_detalles(t=trabajador):
                mostrar_detalles_trabajador(t)
            
            ctk.CTkButton(trabajador_frame, 
                         text="Ver detalles",
                         width=100,
                         command=ver_detalles).grid(row=0, column=2, rowspan=3, padx=10, sticky="e")

    def mostrar_formulario_contratacion(empleador, trabajador, db, ID_servicio=None):
        try:
            ventana = ctk.CTkToplevel()
            ventana.title("Nueva Contratación")
            ventana.geometry("600x500")
            ventana.resizable(False, False)

         
            var_mensaje = tk.StringVar()
            var_fecha = tk.StringVar(value=datetime.now().strftime("%d/%m/%Y"))
            var_modalidad = tk.StringVar(value="presencial")
            var_valor = tk.DoubleVar(value=0.0)

           
            main_frame = ctk.CTkFrame(ventana)
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)

            ctk.CTkLabel(
                main_frame,
                text=f"Contratar a {trabajador.get('nombre', '')}",
                font=("Open Sans", 18, "bold")
            ).pack(pady=(0, 20))

           
            campos = [
                ("Mensaje/Descripción:", "mensaje", "text", var_mensaje),
                ("Fecha (DD/MM/AAAA):", "fecha", "entry", var_fecha),
                ("Modalidad:", "modalidad", "option", var_modalidad, ["presencial", "remoto", "híbrido"]),
                ("Valor acordado:", "valor", "number", var_valor)
            ]

            for label, key, tipo, var, *opts in campos:
                frame = ctk.CTkFrame(main_frame, fg_color="transparent")
                frame.pack(fill="x", pady=5)
                ctk.CTkLabel(frame, text=label).pack(side="left", padx=5)

                if tipo == "text":
                    entry = ctk.CTkTextbox(frame, height=80, width=400)
                    entry.pack(side="right")
                    setattr(main_frame, f"entry_{key}", entry)
                elif tipo == "entry":
                    entry = ctk.CTkEntry(frame, textvariable=var, width=200)
                    entry.pack(side="right")
                    setattr(main_frame, f"entry_{key}", entry)
                elif tipo == "option":
                    option = ctk.CTkOptionMenu(frame, variable=var, values=opts[0])
                    option.pack(side="right")
                    setattr(main_frame, f"option_{key}", option)
                elif tipo == "number":
                    spin = ctk.CTkEntry(frame, textvariable=var, width=100)
                    spin.pack(side="right")
                    setattr(main_frame, f"spin_{key}", spin)

          
            btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            btn_frame.pack(pady=20)

            def guardar_contratacion():
                try:
                    mensaje = main_frame.entry_mensaje.get("1.0", "end-1c").strip()
                    fecha = var_fecha.get().strip()
                    modalidad = var_modalidad.get()
                    valor = var_valor.get()

                    if not mensaje or not fecha:
                        raise ValueError("Todos los campos son obligatorios")
                    if valor <= 0:
                        raise ValueError("El valor debe ser mayor que cero")

                   
                    nueva_contratacion = Contratacion(
                        ID_contratacion=str(uuid.uuid4()),
                        ID_empleador=empleador['ID'],
                        ID_trabajador=trabajador['ID'],
                        fecha_inicio=fecha,
                        estado_contratacion='pendiente',
                        modalidad=modalidad,
                        valor_acordado=valor,
                        ID_servicio=ID_servicio
                    )

                    if nueva_contratacion.registrar_contratacion(db):
                       
                        notificacion = {
                            'ID_notificacion': str(uuid.uuid4()),
                            'ID_usuario': trabajador['ID'],
                            'tipo': 'nueva_contratacion',
                            'mensaje': f"Nueva contratación de {empleador['nombre']}: {mensaje}",
                            'fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'leida': False,
                            'ID_contratacion': nueva_contratacion.ID_contratacion
                        }
                        db.data['notificaciones'].append(notificacion)
                        db.save_data()

                        messagebox.showinfo("Éxito", "Contratación creada correctamente")
                        ventana.destroy()
                    else:
                        raise Exception("No se pudo registrar la contratación")

                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo crear la contratación: {str(e)}")

            ctk.CTkButton(btn_frame, text="Guardar", command=guardar_contratacion).pack(side="left", padx=10)
            ctk.CTkButton(btn_frame, text="Cancelar", command=ventana.destroy).pack(side="right", padx=10)

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo mostrar el formulario: {str(e)}")

    def mostrar_detalles_trabajador(trabajador):
        
        detalles_window = ctk.CTkToplevel(ventana)
        detalles_window.title(f"Detalles de {trabajador.get('nombre', '')}")
        detalles_window.geometry("600x500")
        detalles_window.grab_set()
        
       
        main_frame = ctk.CTkFrame(detalles_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
     
        foto_path = os.path.join(FOTOS_PERFIL_DIR, trabajador.get('foto', ''))
        if not os.path.exists(foto_path):
            foto_path = DEFAULT_PROFILE_PIC
        
        try:
            img = Image.open(foto_path).resize((120, 120))
            photo = ImageTk.PhotoImage(img)
            foto_label = tk.Label(main_frame, image=photo, bg="#FFFFFF")
            foto_label.image = photo
            foto_label.pack(pady=20)
        except:
            pass
        
        
        info_frame = ctk.CTkFrame(main_frame, fg_color="#FFFFFF")
        info_frame.pack(fill="x", padx=50, pady=10)
        
        campos_info = [
            ("Nombre:", trabajador.get('nombre', '')),
            ("Profesión:", trabajador.get('profesion', '')),
            ("Experiencia:", trabajador.get('experiencia_lab', '')),
            ("Contacto:", trabajador.get('contacto', '')),
            ("Habilidades:", trabajador.get('habilidades', '')),
            ("Tarifa:", f"${trabajador.get('tarifa', '')}/hora"),
        ]
        
        for label, value in campos_info:
            frame = ctk.CTkFrame(info_frame, fg_color="transparent")
            frame.pack(fill="x", pady=2)
            
            ctk.CTkLabel(frame, 
                        text=label,
                        font=("Open Sans", 12, "bold"),
                        width=120,
                        anchor="w").pack(side="left")
            
            ctk.CTkLabel(frame, 
                        text=value,
                        font=("Open Sans", 12),
                        wraplength=300).pack(side="left", padx=5)
        
     
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)
        
  
        ctk.CTkButton(btn_frame,
                    text="Contratar",
                    fg_color="#4CAF50",
                    command=lambda: [detalles_window.destroy(), mostrar_formulario_contratacion(usuario, trabajador, db)]).pack(side="left", padx=5, fill="x", expand=True)
        

        ctk.CTkButton(btn_frame,
                    text="Cerrar",
                    fg_color="#F44336",
                    command=detalles_window.destroy).pack(side="right", padx=5, fill="x", expand=True)

    def mostrar_notificacion_individual_empleador(parent, notif, db, usuario):
        frame = ctk.CTkFrame(parent, fg_color="#E3F2FD", corner_radius=10)
        frame.pack(fill="x", padx=5, pady=5, ipady=5)

        header_frame = ctk.CTkFrame(frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(5,0))
        
        tipo_notif = {
            'contratacion_aceptada': 'Contratación Aceptada',
            'contratacion_rechazada': 'Contratación Rechazada',
            'oferta_pendiente': 'Oferta Pendiente',
            'nueva_contratacion': 'Nueva Contratación'
        }.get(notif.get('tipo_nots'), f"{notif.get('tipo_nots')}")
        
        ctk.CTkLabel(header_frame,
            text=f"{tipo_notif} - {notif.get('fecha', '')}",
            font=("Open Sans", 12, "bold"),
            text_color="#0D47A1").pack(side="left")
        
        
        ctk.CTkLabel(frame, text=notif.get('mensaje', ''), font=("Open Sans", 12), wraplength=400).pack(padx=10, pady=5)

    def mostrar_notificaciones_empleador(parent, db, usuario):
        try:
            notificaciones = Notificaciones.obtener_notificaciones_usuario(db, usuario['ID'], no_leidas=False)
            
            if not notificaciones:
                ctk.CTkLabel(parent,
                    text="No tienes notificaciones pendientes",
                    font=("Open Sans", 14)).grid(row=0, column=0, pady=50)
                return
            
            contenedor_scroll = ctk.CTkFrame(parent)
            contenedor_scroll.grid(row=0, column=0, sticky="nsew") 
            
            canvas = tk.Canvas(contenedor_scroll, bg="white", highlightthickness=0)
            scrollbar = ctk.CTkScrollbar(contenedor_scroll, orientation="vertical", command=canvas.yview)
            scrollable_frame = ctk.CTkFrame(canvas, fg_color="white")
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.grid(row=0, column=0, sticky="nsew")
            scrollbar.grid(row=0, column=1, sticky="ns") 

            contenedor_scroll.grid_rowconfigure(0, weight=1)
            contenedor_scroll.grid_columnconfigure(0, weight=1)
            
            for notif in notificaciones:
                mostrar_notificacion_individual_empleador(scrollable_frame, notif, db, usuario)
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar notificaciones: {str(e)}")

    mostrar_notificaciones_empleador(contenedor_notificaciones, db, usuario)

    ventana.protocol("WM_DELETE_WINDOW", lambda: [ventana.destroy(), master.deiconify()])

def inicio_trabajador(master, usuario=None):
    ventanai = ctk.CTkToplevel(master)
    ventanai.title(f"Panel Trabajador - {usuario['nombre']}" if usuario else "Inicio sesión - Trabajador")
    ventanai.geometry("950x750") 
    ventanai.configure(fg_color="#9EC6F3")

    from back import BASE_DIR, FOTOS_PERFIL_DIR, DEFAULT_PROFILE_PIC

    ventanai.grid_columnconfigure(0, weight=0)
    ventanai.grid_columnconfigure(1, weight=1)
    ventanai.grid_rowconfigure(0, weight=1)

    sidebar = tk.Frame(ventanai, bg="#6fa4e1", width=300)
    sidebar.grid(row=0, column=0, sticky="nsew")
    sidebar.grid_propagate(False)

    nombre_foto = usuario.get("foto", "").strip() if usuario else ""

    if nombre_foto:
        ruta_foto_completa = os.path.join(FOTOS_PERFIL_DIR, nombre_foto)
    else:
        ruta_foto_completa = DEFAULT_PROFILE_PIC   
       
    try:
        if os.path.exists(ruta_foto_completa):
            img = Image.open(ruta_foto_completa)
        else:
            raise FileNotFoundError(f"No se encontró el archivo: {ruta_foto_completa}")
            
        img = img.resize((80, 80))
        photo = ImageTk.PhotoImage(img)
        
    except Exception as e:
        try:
            img = Image.open(DEFAULT_PROFILE_PIC).resize((80, 80))
            photo = ImageTk.PhotoImage(img)
        except:
            img = Image.new('RGB', (80, 80), color='#CCCCCC')
            photo = ImageTk.PhotoImage(img)
            
    icono_usuario = tk.Label(sidebar, image=photo, bg="#6fa4e1")
    icono_usuario.image = photo  
    icono_usuario.pack(pady=(20, 10), anchor="nw", padx=10)

    nombre_usuario = usuario['nombre'] if usuario else "Trabajador"
    tk.Label(sidebar, text=nombre_usuario, bg="#6fa4e1", fg="white", font=("Open Sans", 20, "bold")).pack(anchor="nw", padx=10, pady=(0,20))
    
    def eliminar_cuenta():
        if not usuario or 'ID' not in usuario:
            messagebox.showerror("Error", "Datos de usuario incompletos", parent=ventanai)
            return

        if not messagebox.askyesno(
            "Confirmar eliminación",
            "¿Estás seguro de eliminar tu cuenta permanentemente?",
            icon='warning',
            parent=ventanai
        ):
            return

        contraseña_ingresada = simpledialog.askstring(
            "Verificación",
            "Ingresa tu contraseña actual para confirmar:",
            parent=ventanai,
            show='*'
        )

        if not contraseña_ingresada:
            return

        usuario_en_db = next((u for u in db.data['usuarios'] if str(u['ID']) == str(usuario['ID'])), None)

        if not usuario_en_db or str(contraseña_ingresada) != str(usuario_en_db['contraseña']):
            messagebox.showerror("Error", "Contraseña incorrecta", parent=ventanai)
            return

        u = Usuario(
            ID=usuario['ID'],
            nombre=usuario['nombre'],
            contacto=usuario['contacto'],
            contraseña=usuario['contraseña'],
            tipo=usuario['tipo'],
            foto=usuario.get('foto', '')
        )

        if u.eliminar_cuenta(db):
            messagebox.showinfo("Éxito", "Cuenta eliminada correctamente", parent=ventanai)
            ventanai.destroy()
            master.deiconify()
        else:
            messagebox.showerror("Error", "No se pudo eliminar la cuenta", parent=ventanai)
        db.data = db._load_data()

    def editar_cuenta():
        if not usuario or 'ID' not in usuario or 'tipo' not in usuario:
            messagebox.showerror("Error", "Datos de usuario incompletos", parent=ventanai)
            return
        
        user_id = usuario['ID']
        user_type = usuario['tipo']
        
        user_data = db.get_user_by_id(user_id) or {}
        trabajador_data = db.get_trabajador_by_id(user_id) if user_type == 'trabajador' else {}
        
        if not user_data:
            messagebox.showerror("Error", "Usuario no encontrado", parent=ventanai)
            return

        ventanai.withdraw()
        ventanaec = ctk.CTkToplevel()
        ventanaec.title(f"Editar información - {usuario.get('nombre', '')}")
        ventanaec.geometry("800x650")
        ventanaec.configure(fg_color="#BDDDE4")

        
        ventanaec.grid_columnconfigure(0, weight=1)
        ventanaec.grid_columnconfigure(1, weight=2)
        ventanaec.grid_columnconfigure(2, weight=1)

        
        titulo = ctk.CTkLabel(ventanaec,
                            text="Editar información",
                            font=("Open Sans", 30, "bold"),
                            text_color="white")
        titulo.grid(row=0, column=0, columnspan=3, pady=(30, 20))

        def seleccionar_imagen():
            ruta = filedialog.askopenfilename(
                title="Seleccionar imagen",
                filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg")]
            )
            if ruta:
                entries["foto"].delete(0, tk.END)
                entries["foto"].insert(0, ruta)

        
        campos = [
            {"label": "Nombre:", "key": "nombre", "row": 1, "source": "user"},
            {"label": "Contacto:", "key": "contacto", "row": 2, "source": "user"},
            {"label": "Profesión:", "key": "profesion", "row": 3, "source": "trabajador"},
            {"label": "Contraseña actual:", "key": "", "row": 4, "password": True},
            {"label": "Nueva contraseña:", "key": "", "row": 5, "password": True},
            {"label": "Foto de perfil:", "key": "foto", "row": 6, "source": "user"},
            {"label": "Experiencia laboral:", "key": "experiencia_lab", "row": 7, "source": "trabajador"},
            {"label": "Habilidades:", "key": "habilidades", "row": 8, "source": "trabajador"}
        ]

        entries = {}

        for campo in campos:
            row_frame = ctk.CTkFrame(ventanaec, fg_color="transparent")
            row_frame.grid(row=campo["row"], column=0, columnspan=3, sticky="nsew", pady=5)
            row_frame.grid_columnconfigure(1, weight=1)

            lbl = ctk.CTkLabel(row_frame,
                            text=campo["label"],
                            font=("Open Sans", 18, "bold"),
                            anchor="e",
                            width=180)
            lbl.grid(row=0, column=0, padx=(50, 10), sticky="e")

            if campo.get("editable", True):
                entry = ctk.CTkEntry(row_frame,
                                    width=350,
                                    font=("Open Sans", 16),
                                    corner_radius=8)
                
                if campo.get("password"):
                    entry.configure(show="•")
                
                value = ""
                if campo.get("source") == "user":
                    value = user_data.get(campo["key"], "")
                elif campo.get("source") == "trabajador":
                    value = trabajador_data.get(campo["key"], "")
                
                if value:
                    entry.insert(0, str(value))
                
                entry.grid(row=0, column=1, sticky="ew", padx=(0, 20))
                entries[campo["key"] or campo["label"].lower()] = entry

                if campo["key"] == "foto":
                    btn_examinar = ctk.CTkButton(row_frame,
                                                text="Examinar",
                                                width=100,
                                                command=seleccionar_imagen)
                    btn_examinar.grid(row=0, column=2, padx=(0, 50))

        def guardar_cambios():
            user_updates = {}
            trabajador_updates = {}
            
            for campo in campos:
                if not campo.get("editable", True):
                    continue
                    
                key = campo["key"]
                entry = entries.get(key or campo["label"].lower())
                if entry:
                    value = str(entry.get()) if entry.get() else ""
                    
                    if campo.get("source") == "user":
                        user_updates[key] = value
                    elif campo.get("source") == "trabajador":
                        trabajador_updates[key] = value
            
            nueva_contraseña = entries.get("nueva contraseña:", "").get()
            if nueva_contraseña:
                contraseña_actual = entries.get("contraseña actual:", "").get()
                if str(contraseña_actual) != str(user_data.get("contraseña", "")):
                    messagebox.showerror("Error", "Contraseña actual incorrecta", parent=ventanaec)
                    return
                user_updates["contraseña"] = str(nueva_contraseña)
            
            success = db.update_user(str(usuario['ID']), user_updates)
            if user_type == 'trabajador':
                success &=  db.update_trabajador(str(usuario['ID']), trabajador_updates)
            
            if success:
                messagebox.showinfo("Éxito", "Cambios guardados correctamente", parent=ventanaec)
                ventanaec.destroy()
                ventanai.deiconify()
               
                usuario.update(user_updates)
                if user_type == 'trabajador':
                    usuario.update(trabajador_updates)
            else:
                messagebox.showerror("Error", "No se pudieron guardar los cambios", parent=ventanaec)

        btn_frame = ctk.CTkFrame(ventanaec, fg_color="transparent")
        btn_frame.grid(row=9, column=0, columnspan=3, pady=20)

        btn_aceptar = ctk.CTkButton(btn_frame,
                                text="Aceptar",
                                width=120,
                                height=40,
                                fg_color="#FFF1D5",
                                text_color="black",
                                font=("Open Sans", 15, "bold"),
                                command=guardar_cambios)
        btn_aceptar.pack(side="left", padx=20)

        btn_cancelar = ctk.CTkButton(btn_frame,
                                    text="Cancelar",
                                    width=120,
                                    height=40,
                                    fg_color="#FFF1D5",
                                    text_color="black",
                                    font=("Open Sans", 15, "bold"),
                                    command=lambda: [ventanaec.destroy(), ventanai.deiconify()])
        btn_cancelar.pack(side="right", padx=20)

        ventanaec.protocol("WM_DELETE_WINDOW", lambda: [ventanaec.destroy(), ventanai.deiconify()])

    def curric():
        if not usuario or 'ID' not in usuario:
            messagebox.showerror("Error", "No se pudo identificar al usuario")
            return
        
        ID_trabajador = str(usuario['ID'])
        
       
        if 'curriculums' not in db.tables:
            messagebox.showerror("Error", "Configuración de base de datos incompleta")
            return
        
       
        try:
            with open(db.tables['curriculums'], mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                curriculums = list(reader)
        except FileNotFoundError:
            curriculums = []
        
       
        cv_data = next((c for c in curriculums if str(c.get('ID_trabajador')) == ID_trabajador), None)
        
        is_new = not bool(cv_data)
        
        if is_new:
            cv_data = {
                'ID_cv': str(uuid.uuid4()),
                'ID_trabajador': ID_trabajador,
                'profesion': '',
                'formacion_academica': '',
                'experiencia_profesional': '',
                'habilidades': '',
                'certificaciones': '',
                'idiomas': '',
                'portafolio': '',
                'fecha_last_actualizacion': datetime.now().isoformat()
            }

       
        def guardar_cv():
            try:
              
                updates = {
                    'profesion': entries['profesion'].get(),
                    'formacion_academica': entries['formacion_academica'].get("1.0", "end-1c"),
                    'experiencia_profesional': entries['experiencia_profesional'].get("1.0", "end-1c"),
                    'habilidades': entries['habilidades'].get(),
                    'certificaciones': entries['certificaciones'].get(),
                    'idiomas': entries['idiomas'].get(),
                    'portafolio': entries['portafolio'].get("1.0", "end-1c"),
                    'fecha_last_actualizacion': datetime.now().isoformat()
                }
                
               
                cv_data.update(updates)
                
                
                if is_new:
                    curriculums.append(cv_data)
                else:
                    for i, cv in enumerate(curriculums):
                        if cv['ID_cv'] == cv_data['ID_cv']:
                            curriculums[i] = cv_data
                            break
                
             
                db.data['curriculums'] = curriculums
                
               
                if db.save_data():
                    messagebox.showinfo("Éxito", "Currículum guardado correctamente", parent=ventana_cv)
                    ventana_cv.destroy()
                else:
                    messagebox.showerror("Error", "No se pudo guardar el currículum", parent=ventana_cv)
                    
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {str(e)}", parent=ventana_cv)

     
        ventana_cv = ctk.CTkToplevel()
        ventana_cv.title("Gestión de Currículum")
        ventana_cv.geometry("900x750")
        ventana_cv.configure(fg_color="#BDDDE4")
        
        main_frame = ctk.CTkScrollableFrame(ventana_cv, fg_color="#BDDDE4")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        entries = {}
        
      
        def create_field(label, row, key, multiline=False):
            frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            frame.grid(row=row, column=0, sticky="ew", pady=(10, 0))
            
            lbl = ctk.CTkLabel(frame, text=label, font=("Open Sans", 14, "bold"))
            lbl.pack(side="top", anchor="w")
            
            if multiline:
                entry = ctk.CTkTextbox(frame, height=100, font=("Open Sans", 12))
                entry.insert("1.0", cv_data.get(key, ''))
            else:
                entry = ctk.CTkEntry(frame, font=("Open Sans", 12))
                entry.insert(0, cv_data.get(key, ''))
            
            entry.pack(fill="x", pady=(5, 0))
            entries[key] = entry
        
       
        create_field("Profesión:", 0, 'profesion')
        create_field("Formación Académica:", 1, 'formacion_academica', multiline=True)
        create_field("Experiencia Profesional:", 2, 'experiencia_profesional', multiline=True)
        create_field("Habilidades (separadas por comas):", 3, 'habilidades')
        create_field("Certificaciones (separadas por comas):", 4, 'certificaciones')
        create_field("Idiomas (separados por comas):", 5, 'idiomas')
        create_field("Portafolio (un proyecto por línea):", 6, 'portafolio', multiline=True)
        
      
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.grid(row=7, column=0, sticky="ew", pady=20)
        
        btn_guardar = ctk.CTkButton(
            btn_frame,
            text="GUARDAR CAMBIOS" if not is_new else "CREAR CURRÍCULUM",
            command=guardar_cv,
            fg_color="#4CAF50",
            hover_color="#45a049",
            font=("Open Sans", 14, "bold")
        )
        btn_guardar.pack(side="left", padx=10)
        
        btn_cancelar = ctk.CTkButton(
            btn_frame,
            text="CANCELAR",
            command=ventana_cv.destroy,
            fg_color="#f44336",
            hover_color="#d32f2f",
            font=("Open Sans", 14, "bold")
        )
        btn_cancelar.pack(side="right", padx=10)
        
        ventana_cv.grab_set()  

    def mostrar_estadisticas():
        try:
           
            ventana_stats = ctk.CTkToplevel()
            ventana_stats.title("Estadísticas y Análisis")
            ventana_stats.geometry("1200x800")
            ventana_stats.configure(fg_color="#BDDDE4")

            ventana_stats.protocol("WM_DELETE_WINDOW", lambda: on_close(ventana_stats))

            
            estadisticas = Estadistica(db)

            
            tabview = ctk.CTkTabview(ventana_stats)
            tabview.pack(fill="both", expand=True, padx=10, pady=10)

            
            tab_habilidades = tabview.add("Habilidades")
            frame_habilidades = ctk.CTkScrollableFrame(tab_habilidades)
            frame_habilidades.pack(fill="both", expand=True)

            
            fig1 = estadisticas.graficar_habilidades_mas_demandadas()
            canvas1 = FigureCanvasTkAgg(fig1, master=frame_habilidades)
            canvas1.draw()
            canvas1.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

           
            fig2 = estadisticas.graficar_habilidades_mas_ofrecidas()
            canvas2 = FigureCanvasTkAgg(fig2, master=frame_habilidades)
            canvas2.draw()
            canvas2.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

            
            fig3 = estadisticas.graficar_brecha_demanda_oferta()
            canvas3 = FigureCanvasTkAgg(fig3, master=frame_habilidades)
            canvas3.draw()
            canvas3.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

          
            tab_tendencias = tabview.add("Tendencias")
            frame_tendencias = ctk.CTkScrollableFrame(tab_tendencias)
            frame_tendencias.pack(fill="both", expand=True)

            fig4 = estadisticas.graficar_servicios_por_mes()
            if fig4:
                canvas4 = FigureCanvasTkAgg(fig4, master=frame_tendencias)
                canvas4.draw()
                canvas4.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

           
            fig5 = estadisticas.graficar_contrataciones_por_mes()
            if fig5:
                canvas5 = FigureCanvasTkAgg(fig5, master=frame_tendencias)
                canvas5.draw()
                canvas5.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

           
            tab_recomendaciones = tabview.add("Recomendaciones")
            frame_recomendaciones = ctk.CTkScrollableFrame(tab_recomendaciones)
            frame_recomendaciones.pack(fill="both", expand=True)

            
            recomendaciones = estadisticas.consultar_analisis_DemandaOferta()
            for i, recomendacion in enumerate(recomendaciones):
                label = ctk.CTkLabel(frame_recomendaciones, text=f"• {recomendacion}", font=("Arial", 14))
                label.pack(pady=5, padx=10, anchor="w")

            ventana_stats.grab_set()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron mostrar las estadísticas: {str(e)}")
            if 'ventana_stats' in locals():
                ventana_stats.destroy()
                
    def on_close(window):
        window.destroy()
        window.quit()

    btn_eliminar = ctk.CTkButton(sidebar, 
                                text="Eliminar perfil", 
                                font=("Open Sans", 15, "bold"),
                                fg_color="#FF6B6B", 
                                text_color="white", 
                                width=200, 
                                height=40, 
                                command=eliminar_cuenta)
    btn_eliminar.pack(side="bottom", pady=(0,30))

    btn_editar = ctk.CTkButton(sidebar, 
                              text="Editar perfil", 
                              font=("Open Sans", 15, "bold"),
                              fg_color="#FFF1D5", 
                              text_color="black", 
                              width=200, 
                              height=40, 
                              command=editar_cuenta)
    btn_editar.pack(pady=(20, 10))
    btn_curriculo = ctk.CTkButton(sidebar, 
                              text="Currículo", 
                              font=("Open Sans", 15, "bold"),
                              fg_color="#FFF1D5", 
                              text_color="black", 
                              width=200, 
                              height=40, 
                              command=curric)
    btn_curriculo.pack(pady=(0, 10))
    btn_estadísticas = ctk.CTkButton(sidebar, 
                              text="Estadísticas", 
                              font=("Open Sans", 15, "bold"),
                              fg_color="#FFF1D5", 
                              text_color="black", 
                              width=200, 
                              height=40, 
                              command=mostrar_estadisticas)
    btn_estadísticas.pack(pady=(0, 20))

    main_frame = ctk.CTkFrame(ventanai, fg_color="#9EC6F3")
    main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
    main_frame.grid_columnconfigure(0, weight=1)
    main_frame.grid_rowconfigure(0, weight=1)
    
    notificaciones_frame = ctk.CTkFrame(main_frame, fg_color="#FFFFFF")
    notificaciones_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    notificaciones_frame.grid_columnconfigure(0, weight=1)
    notificaciones_frame.grid_rowconfigure(1, weight=1)

    ctk.CTkLabel(notificaciones_frame, text="Notificaciones y Contrataciones", font=("Open Sans", 18, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=10)

    def mostrar_nueva_contratacion(parent, notif, db, usuario):
        try:
            contrataciones = Contratacion.obtener_contrataciones(
                db, ID_usuario=notif['ID_usuario'], tipo_usuario='trabajador')
            
            if not contrataciones:
                raise ValueError("No se encontraron contrataciones para este usuario")
            
            contratacion = next(
                (c for c in contrataciones 
                if str(c['ID_contratacion']) == str(notif.get('ID_contratacion'))), 
                None)
            
            if not contratacion:
                raise ValueError("Contratación específica no encontrada")
            
            empleador = db.get_user_by_id(contratacion.get('ID_empleador')) or {}
            
            detalles_frame = ctk.CTkFrame(parent, fg_color="transparent")
            detalles_frame.pack(fill="x", padx=10, pady=5)
            
            detalles = [
                f"Fecha inicio: {contratacion.get('fecha_inicio', 'No especificada')}",
                f"Empleador: {empleador.get('nombre', 'Desconocido')}",
                f"Modalidad: {contratacion.get('modalidad', 'No especificada')}",
                f"Valor acordado: ${float(contratacion.get('valor_acordado', 0)):,.2f}"
            ]
            
            for detalle in detalles:
                ctk.CTkLabel(detalles_frame, 
                            text=detalle, 
                            font=("Open Sans", 12)).pack(anchor="w")
            
            btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
            btn_frame.pack(fill="x", padx=10, pady=(5,10))
            
            def aceptar():
                try:
                    Notificaciones.marcar_como_leida(db, notif['ID_notificacion'])
                    
                    Contratacion.actualizar_estado(
                        db, 
                        notif['ID_contratacion'], 
                        nuevo_estado="aceptado"
                    )
                    
                    notif_respuesta = Notificaciones(
                        ID_emisor=usuario['ID'],
                        ID_destinatario=contratacion['ID_empleador'],
                        mensaje=f"{usuario['nombre']} ha aceptado tu oferta",
                        tipo="contratacion_aceptada",
                        ID_contratacion=notif['ID_contratacion']
                    )
                    notif_respuesta.enviar_nots(db)
                    
                    messagebox.showinfo("Éxito", "Contratación aceptada correctamente")
                    parent.destroy()
                    
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo aceptar: {str(e)}")

            def rechazar():
                try:
                    Notificaciones.marcar_como_leida(db, notif['ID_notificacion'])
                    
                    Contratacion.actualizar_estado(
                        db, 
                        notif['ID_contratacion'], 
                        nuevo_estado="rechazado"
                    )
                    
                    notif_respuesta = Notificaciones(
                        ID_emisor=usuario['ID'],
                        ID_destinatario=contratacion['ID_empleador'],
                        mensaje=f"{usuario['nombre']} ha rechazado tu oferta",
                        tipo="contratacion_rechazada",
                        ID_contratacion=notif['ID_contratacion']
                    )
                    notif_respuesta.enviar_nots(db)
                    
                    messagebox.showinfo("Éxito", "Contratación rechazada correctamente")
                    parent.destroy()
                    
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo rechazar: {str(e)}")

            ctk.CTkButton(
                btn_frame, 
                text=" Aceptar", 
                fg_color="#4CAF50",
                hover_color="#388E3C",
                command=aceptar
            ).pack(side="left", expand=True, padx=5, fill="x")
            
            ctk.CTkButton(
                btn_frame, 
                text=" Rechazar", 
                fg_color="#F44336",
                hover_color="#D32F2F",
                command=rechazar
            ).pack(side="right", expand=True, padx=5, fill="x")

        except Exception as e:
            messagebox.showerror("Error", 
                            f"No se pudo mostrar la contratación:\n{str(e)}\n\n"
                            f"Notificación: {notif}\n"
                            f"Usuario: {usuario}")

    def mostrar_oferta_pendiente(parent, notif, db, usuario):
        try:
           
            detalles_frame = ctk.CTkFrame(parent, fg_color="transparent")
            detalles_frame.pack(fill="x", padx=10, pady=5)

            emisor = notif.get('emisor', {})
            detalles = [
                f"De: {emisor.get('nombre', 'Empleador')}",
                f"{notif.get('mensaje', 'Sin título')}",
                f"Fecha: {notif.get('fecha_envio', 'No especificada')}"
            ]
            
            for detalle in detalles:
                lbl = ctk.CTkLabel(detalles_frame, 
                                text=detalle,
                                font=("Open Sans", 12))
                lbl.pack(anchor="w")
            
            btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
            btn_frame.pack(fill="x", padx=10, pady=(5,10))

            btn_frame.grid_columnconfigure(0, weight=1)
            btn_frame.grid_columnconfigure(1, weight=1)
            
            def responder_oferta(aceptada: bool):
                resultado = procesar_respuesta_oferta(parent, notif['ID_notificacion'], aceptada, db, usuario)
                if resultado:
                    parent.destroy()
            
            ctk.CTkButton(btn_frame,
                text="Aceptar", fg_color="#4CAF50",
                command=lambda: responder_oferta(True)).pack(side="left", expand=True, padx=5)

            
            ctk.CTkButton(btn_frame,
                text="Rechazar", fg_color="#F44336",
                command=lambda: responder_oferta(False)).pack(side="right", expand=True, padx=5)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo mostrar la oferta: {str(e)}")

        def procesar_respuesta_oferta(parent_window, id_notificacion, aceptada, db, usuario):
            try:
               
                accion = "aceptar" if aceptada else "rechazar"
                if not messagebox.askyesno("Confirmar", f"¿{accion.capitalize()} esta oferta?", parent=parent_window):
                    return False
                
               
                Notificaciones.marcar_como_leida(db, id_notificacion)
                
                
                notif_original = next(
                    (n for n in db.data['notificaciones'] if n['ID_notificacion'] == id_notificacion), None)
                
                if not notif_original:
                    raise ValueError("Notificación original no encontrada")
                
               
                tipo_respuesta = f"contratacion_{'aceptada' if aceptada else 'rechazada'}"
                mensaje_respuesta = f"{usuario['nombre']} ha {accion}do tu oferta"
                
                nueva_notificacion = Notificaciones(
                    ID_notificacion=str(uuid.uuid4()),
                    ID_usuario=notif_original['ID_emisor'],
                    ID_emisor=usuario['ID'],
                    mensaje=mensaje_respuesta,
                    tipo_nots=tipo_respuesta,
                    fecha_envio=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    leida="pendiente",
                    ID_servicio=notif_original.get('ID_servicio')
                )
                
              
                if aceptada and notif_original.get('ID_servicio'):
                    servicio = next(
                        (s for s in db.data['servicios'] if s['ID_servicio'] == notif_original['ID_servicio']), None)
                    
                    if servicio:
                        nueva_contratacion = Contratacion(
                            ID_contratacion=str(uuid.uuid4()),
                            ID_empleador=servicio['ID_empleador'],
                            ID_trabajador=usuario['ID'],
                            fecha_inicio=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            estado_contratacion="activa",
                            modalidad=servicio.get('modalidad', 'presencial'),
                            valor_acordado=float(servicio.get('valor', 0)),
                            ID_servicio=servicio['ID_servicio']
                        )
                        
                        if not nueva_contratacion.registrar_contratacion(db):
                            raise Exception("No se pudo registrar la contratación")
                
                
                if not nueva_notificacion.enviar_nots(db):
                    raise Exception("No se pudo enviar la notificación")
                
                messagebox.showinfo("Éxito", f"Oferta {accion}da correctamente", parent=parent_window)
                return True
                
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo procesar la respuesta: {str(e)}", parent=parent_window)
                return False

    def mostrar_notificacion_individual(parent, notif, db, usuario):
        parent.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkFrame(parent, fg_color="#E3F2FD", corner_radius=10)
        frame.pack(fill="x", padx=5, pady=5, ipady=5)

        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(5,0))
        
        tipo_notif = {
            'oferta_pendiente': 'Oferta Pendiente',
            'nueva_contratacion': 'Nueva Contratación',
            'contratacion_aceptada': 'Contratación Aceptada',
            'contratacion_rechazada': 'Contratación Rechazada'
        }.get(notif.get('tipo'), f"{notif.get('tipo')}")
        
        lbl_tipo = ctk.CTkLabel(header_frame,
                            text=f"{tipo_notif} - {notif.get('fecha', '')}",
                            font=("Open Sans", 12, "bold"),
                            text_color="#0D47A1")
        lbl_tipo.pack(side="left")
        
        if notif['tipo'] == 'oferta_pendiente':
            mostrar_oferta_pendiente(frame, notif, db, usuario)
        elif notif['tipo'] == 'nueva_contratacion':
            mostrar_nueva_contratacion(frame, notif, db, usuario)

    def mostrar_notificaciones_trabajador(parent, db, usuario):
        print(f"ID usuario para buscar notificaciones: {usuario['ID']}")
        try:
            for widget in parent.winfo_children():
                widget.destroy()
            
            csv_path = db.tables['notificaciones']
            notificaciones = []

            try:
                with open(csv_path, mode='r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row['ID_usuario'] == str(usuario['ID']):
                            notificaciones.append(row)
            except FileNotFoundError:
                print(f"[ERROR] Archivo de notificaciones no encontrado: {csv_path}")
            except Exception as e:
                print(f"[ERROR] Error leyendo CSV: {str(e)}")

            print(f"[DEBUG] Notificaciones encontradas: {len(notificaciones)}")
            
            if not notificaciones:
                lbl_vacio = ctk.CTkLabel(parent, 
                                    text="No tienes notificaciones pendientes",
                                    font=("Open Sans", 14))
                lbl_vacio.pack(pady=50)
                return
            
            contenedor = ctk.CTkScrollableFrame(parent, fg_color="#FFFFFF")
            contenedor.pack(fill="both", expand=True, padx=10, pady=10)
            
            notificaciones.sort(key=lambda x: x.get('fecha', ''), reverse=True)

            for notif in notificaciones:
                frame_notif = ctk.CTkFrame(contenedor, 
                                        fg_color="#E3F2FD", 
                                        corner_radius=10)
                frame_notif.pack(fill="x", padx=5, pady=5, ipady=5)
                
                mostrar_notificacion_individual(frame_notif, notif, db, usuario)

        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar notificaciones: {str(e)}")
            print(f"Error completo: {traceback.format_exc()}")
                
        
    mostrar_notificaciones_trabajador(notificaciones_frame, db, usuario)
          
    
   
    ventanai.protocol("WM_DELETE_WINDOW", lambda: [ventanai.destroy(), master.deiconify()])


def ventana_registrarse(master):
    ventana_reg=ctk.CTkToplevel(master)
    ventana_reg.title("Registro")
    ventana_reg.geometry("950x750") 
    ventana_reg.configure(fg_color="#9FB3DF")

    def seleccionar_imagen(entry_widget):
        from tkinter import filedialog
        ruta= filedialog.askopenfilename(
            title= "Seleccionar imagen",
            filetypes=[("Imágenes", "**.png;*.jpg;*.jpeg;*.gif")])
        if ruta:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, ruta)

    def registro_empleador():
        ventana_reg.withdraw()

        ventanare =ctk.CTkToplevel(ventana_reg)
        ventanare.title("Registro-empleador")
        ventanare.geometry("950x750")
        ventanare.configure(fg_color="#9FB3DF")

        ventanare.grid_columnconfigure(0, weight=1)
        ventanare.grid_columnconfigure(1, weight=0)
        ventanare.grid_columnconfigure(2, weight=0)
        ventanare.grid_columnconfigure(3, weight=0)
        ventanare.grid_columnconfigure(4, weight=1)

        tk.Label(ventanare, bg="#9FB3DF", text="¡EMPLEADOR!", font=("Open Sans", 50, "bold"), fg="white").grid(row=0, column=0, columnspan=5, pady=20)
        tk.Label(ventanare, bg="#9FB3DF", text="Necesitamos más información para acercate con tu próximo trabajador.", font=("Open Sans", 20), fg="black", wraplength=800).grid(row=1, column=0, columnspan=5, pady=10)

        etiquetas=["Empresa:", "Contacto:", "Método de pago:", "Contraseña:", "Foto de perfil:"]
        placeholders= ["Nombre de la empresa", "Teléfono o email","Trjeta/Transferencia","Contraseña","Ruta de imagen"]

        entries={}

        for i, (label_text, placeholder) in enumerate(zip(etiquetas, placeholders)):
            tk.Label(ventanare, text= label_text, font=("Open Sans", 18, "bold"), fg="black", bg="#9FB3DF").grid(row=i+2, column=0, sticky="e", padx=40, pady=10)

            if "foto" in label_text.lower():
                entry= ctk.CTkEntry(ventanare, placeholder_text=placeholder, width=300)
                browse_btn= ctk.CTkButton(ventanare, text="Examinar", width=80, command= lambda e=entry: seleccionar_imagen(e))
                entry.grid(row=i+2, column=1, padx=(5,0), pady=10, sticky="w")
                browse_btn.grid(row=i+2, column=2, padx=(0,5), sticky="w")
            else:
                entry=ctk.CTkEntry(ventanare, placeholder_text=placeholder, width=300)
                if "contraseña" in label_text.lower():
                    entry.configure(show="*")
                entry.grid(row=i+2, column=1, sticky= "w", padx=5, pady=10)

            entries[label_text]=entry

        def registrar():
            datos= {campo: entry.get() for campo, entry in entries.items()}
            nombre_empresa= datos["Empresa:"]
            contacto = datos["Contacto:"]
            metodo_pago = datos["Método de pago:"]
            contraseña = datos["Contraseña:"]
            ruta_foto = datos["Foto de perfil:"]

            nombre_foto_final=""
            if ruta_foto:
                try:
                    os.makedirs(FOTOS_PERFIL_DIR, exist_ok=True)

                    ext= os.path.splitext(ruta_foto)[1]
                    nombre_foto_final=f'{generar_id()}{ext}'
                    destino= os.path.join(FOTOS_PERFIL_DIR, nombre_foto_final)

                    shutil.copy(ruta_foto, destino)
                    
                except Exception as e:
                    messagebox.showwarning("Advertencia", f"No se pudo guardar la imagen: {e}")
                    ruta_foto = ""

            if not all([nombre_empresa, contacto, metodo_pago, contraseña]):
                messagebox.showerror("Error", "Por favor completa los campos.")
                return
            
            if any(u['contacto']==contacto for u in db.data['usuarios']):
                messagebox.showerror("Error", "Ya existe un usuario con ese contacto.")
                return
            
            ID= generar_id()
            nuevo_empleador= Empleador(ID=ID, 
                                       nombre=nombre_empresa, 
                                       contacto=contacto, 
                                       contraseña=contraseña, 
                                       foto=ruta_foto, 
                                       metodo_pago=metodo_pago)
            nuevo_empleador.reg_usuario(db)
            db.save_data()

            if ruta_foto:
                try:
                    with open(ruta_foto, "rb") as f:
                        class FileMock:
                            def __init__(self, filename, content):
                                self.filename = filename
                                self.content = content
                                self.stream = content
                            def seek(self, *args): return self.content.seek(*args)
                            def tell(self): return self.content.tell()
                            def save(self, path): open(path, "wb").write(self.content.read())
                        file = FileMock(os.path.basename(ruta_foto),f)
                        f.seek(0)
                        if not nuevo_empleador.subir_foto(db, file):
                            messagebox.showwarning("Advertencia", "La imagen no pudo ser cargada")
                        db.save_data()
                except Exception as e:
                    messagebox.showwarning("Advertencia", f"No se pudo cargar la foto: {e}")

            
            messagebox.showinfo("Registro exitoso", "¡Empleador registrado correctamente!")
            ventanare.destroy()
            ventana_reg.destroy()
            master.deiconify()

        ctk.CTkButton(ventanare, text="Registrarse", font=("Open Sans",30, "bold"),fg_color="#FFF1D5", text_color="black", width=200, height=70, command=registrar).grid(row= len(etiquetas)+3, column=0, columnspan=5, pady=30)

        ventanare.protocol("WM_DELETE_WINDOW", lambda: [ventanare.destroy(), ventana_reg.deiconify()])
    
    def registro_trabajador():
        ventana_reg.withdraw()

        ventanart = ctk.CTkToplevel(ventana_reg)
        ventanart.title("Registro-trabajador")
        ventanart.geometry("950x750")
        ventanart.configure(fg_color="#9FB3DF")

        
        ventanart.grid_columnconfigure(0, weight=1)
        ventanart.grid_columnconfigure(1, weight=0)
        ventanart.grid_columnconfigure(2, weight=0)
        ventanart.grid_columnconfigure(3, weight=0)
        ventanart.grid_columnconfigure(4, weight=1)

        
        ctk.CTkLabel(ventanart, 
                    text="¡TRABAJADOR!", 
                    font=("Open Sans", 50, "bold"), 
                    text_color="white",
                    bg_color="#9FB3DF").grid(row=0, column=0, columnspan=5, pady=20)
        
        ctk.CTkLabel(ventanart, 
                    text="Necesitamos más información para acercarte con tu próximo empleador.", 
                    font=("Open Sans", 20), 
                    text_color="black",
                    bg_color="#9FB3DF",
                    wraplength=800).grid(row=1, column=0, columnspan=5, pady=10)

        
        etiquetas = ["Nombre:", "Contacto:", "Contraseña:", "Foto de perfil:", "Profesión:", "Experiencia:", "Disponibilidad:"]
        placeholders = ["Nombre completo", "Teléfono o email", "Contraseña", "Ruta de imagen", "Tu profesión principal", "Años de experiencia", "Seleccione disponibilidad"]

        entries = {}

        def seleccionar_imagen(entry_widget):
            ruta = filedialog.askopenfilename(
                title="Seleccionar imagen",
                filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg")]
            )
            if ruta:
                entry_widget.delete(0, tk.END)
                entry_widget.insert(0, ruta)

        for i, (label_text, placeholder) in enumerate(zip(etiquetas, placeholders)):
           
            ctk.CTkLabel(ventanart, 
                        text=label_text,
                        font=("Open Sans", 18, "bold"),
                        text_color="black",
                        bg_color="#9FB3DF").grid(row=i+2, column=0, sticky="e", padx=20, pady=10)

            
            if "foto" in label_text.lower():
                entry = ctk.CTkEntry(ventanart, 
                                placeholder_text=placeholder, 
                                width=300)
                browse_btn = ctk.CTkButton(ventanart, 
                                        text="Examinar", 
                                        width=90,
                                        command=lambda e=entry: seleccionar_imagen(e))
                entry.grid(row=i+2, column=1, padx=(5,0), pady=10, sticky="w")
                browse_btn.grid(row=i+2, column=2, padx=(0,5), sticky="w")
            elif "disponibilidad" in label_text.lower():
                disponibilidad_opciones = [
                    "Tiempo completo",
                    "Medio tiempo", 
                    "Por horas",
                    "Freelance",
                    "Por proyecto"
                ]
                combobox = ctk.CTkComboBox(ventanart,
                                        values=disponibilidad_opciones,
                                        width=300)
                combobox.grid(row=i+2, column=1, sticky="w", padx=5, pady=10)
                entries[label_text] = combobox
                continue
            else:
                entry = ctk.CTkEntry(ventanart, 
                                placeholder_text=placeholder, 
                                width=300)
                if "contraseña" in label_text.lower():
                    entry.configure(show="•")
                entry.grid(row=i+2, column=1, sticky="w", padx=5, pady=10)

            entries[label_text] = entry

        def registrar():
            try:
               
                datos = {
                    "nombre": entries["Nombre:"].get(),
                    "contacto": entries["Contacto:"].get(),
                    "contraseña": entries["Contraseña:"].get(),
                    "foto": entries["Foto de perfil:"].get(),
                    "profesion": entries["Profesión:"].get(),
                    "experiencia": entries["Experiencia:"].get(),
                    "disponibilidad": entries["Disponibilidad:"].get().lower().replace(" ", "_")
                }

              
                if not all(datos.values()):
                    messagebox.showerror("Error", "Todos los campos son obligatorios", parent=ventanart)
                    return

                if len(datos["contraseña"]) < 8:
                    messagebox.showerror("Error", "La contraseña debe tener al menos 8 caracteres", parent=ventanart)
                    return

               
                from back import generar_id, Trabajador
                user_id = generar_id()
                
                trabajador = Trabajador(
                    ID=user_id,
                    nombre=datos["nombre"],
                    contacto=datos["contacto"],
                    contraseña=datos["contraseña"],
                    foto=datos["foto"],
                    profesion=datos["profesion"],
                    experiencia_laboral=datos["experiencia"],
                    disponibilidad=datos["disponibilidad"],
                )

                
                if trabajador.reg_usuario(db):
                    messagebox.showinfo("Éxito", "Registro completado exitosamente", parent=ventanart)
                    ventanart.destroy()
                    ventana_reg.deiconify()
                else:
                    messagebox.showerror("Error", "El contacto ya está registrado", parent=ventanart)

            except Exception as e:
                messagebox.showerror("Error", f"Ocurrió un error: {str(e)}", parent=ventanart)
                print(f"Error en registro: {str(e)}")

        
        ctk.CTkButton(ventanart,
                    text="Registrarse",
                    font=("Open Sans", 30, "bold"),
                    fg_color="#FFF1D5",
                    text_color="black",
                    width=200,
                    height=70,
                    command=registrar).grid(row=len(etiquetas)+3, column=0, columnspan=5, pady=30)

        ventanart.protocol("WM_DELETE_WINDOW", lambda: [ventanart.destroy(), ventana_reg.deiconify()])


    tk.Label(ventana_reg, text="Soy un ...", font=("Open Sans", 60, "bold"), bg="#9FB3DF", fg="white").pack(pady=60)
    
    frame_botones = ctk.CTkFrame(ventana_reg, fg_color="#9FB3DF")
    frame_botones.pack(pady=20)

    btn_Empleador=ctk.CTkButton(frame_botones, text="Empleador", font=("Open Sans", 40, "bold"), bg_color="#9FB3DF", border_color="#FFF1D5", fg_color="#FFF1D5", text_color= "black",
                            width=300, height=100, command=registro_empleador)
    btn_Empleador.pack(side=ctk.LEFT,  padx=20)

    btn_Trabajador=ctk.CTkButton(frame_botones, text="Trabajador", font=("Open Sans", 40, "bold"), bg_color="#9FB3DF", border_color="#FFF1D5", fg_color="#FFF1D5", text_color= "black",
                            width=300, height=100, command=registro_trabajador)
    btn_Trabajador.pack(side=ctk.LEFT,  padx=20)
    
    ventana_reg.protocol("WM_DELETE_WINDOW", lambda: [ventana_reg.destroy(), master.deiconify()])
    
def Ventana_inicio():
    ventana=ctk.CTk()
    ventana.title("Ventana de inicio")
    ventana.geometry("950x750") 
    ventana.configure(fg_color="#9FB3DF")
    ventana.grid_columnconfigure(0, weight=1)
    
    def inicio_sesion_empleador(master):
        master.withdraw()

        ventanaise= ctk.CTkToplevel(master)
        ventanaise.title("Inicio sesión - Empleador")
        ventanaise.geometry("950x750") 
        ventanaise.configure(fg_color="#9FB3DF")

        ventanaise.grid_columnconfigure(0, weight=1)
        ventanaise.grid_columnconfigure(1, weight=0)
        ventanaise.grid_columnconfigure(2, weight=1)

        tk.Label(ventanaise, bg="#9FB3DF", text="¡EMPLEADOR!", font=("Open Sans", 50, "bold"), fg="white").grid(row=0, column=0, columnspan=3, pady=20)
        tk.Label(ventanaise, bg="#9FB3DF", text="Ingresa tu información para iniciar sesion.", font=("Open Sans", 20), fg="black", wraplength=800).grid(row=1, column=0, columnspan=3, pady=10)

        etiquetas=["Contacto:", "Contraseña:"]
        placeholders= ["Teléfono/email","Contraseña"]

        entries={}

        for i, (label_text, placeholder) in enumerate(zip(etiquetas, placeholders)):
            tk.Label(ventanaise, text= label_text, font=("Open Sans", 18, "bold"), fg="black", bg="#9FB3DF").grid(row=i+2, column=0, sticky="e", padx=40, pady=10)
            entry=ctk.CTkEntry(ventanaise, placeholder_text=placeholder, width=300)                
            if "contraseña" in label_text.lower():
                entry.configure(show="*")
            entry.grid(row=i+2, column=1, sticky= "w", padx=5, pady=10)
            entries[label_text]=entry

        def verificar_datos():
            contacto= entries["Contacto:"].get().strip()
            contraseña= entries["Contraseña:"].get().strip()

            if not contacto or not contraseña: 
                messagebox.showerror("Error", "Ingresa contacto y contraseña.")
                return
            
            usuario_dummy=Usuario("","","","","")
            usuario=usuario_dummy.iniciar_sesion(db,contacto, contraseña)

            if usuario and usuario["tipo"].lower() == "empleador":
                messagebox.showinfo("Inicio de sesión", f'Bienvenido {usuario['nombre']}!!')
                ventanaise.destroy()
                inicio_empleador(ventana, usuario)
            else:
                messagebox.showerror("Error", "Contacto o contraseña incorrectos.")

        ctk.CTkButton(ventanaise, text="Ingresar", font=("Open Sans",30, "bold"),fg_color="#FFF1D5", text_color="black", width=200, height=70, command=verificar_datos).grid(row= len(etiquetas)+3, column=0, columnspan=3, pady=30)
        ventanaise.protocol("WM_DELETE_WINDOW", lambda: [ventanaise.destroy(), master.deiconify()])     
      
    def inicio_sesion_trabajador(master):
        master.withdraw()

        ventanaist = ctk.CTkToplevel(master)
        ventanaist.title("Inicio sesión - Trabajador")
        ventanaist.geometry("950x750") 
        ventanaist.configure(fg_color="#9FB3DF")
        ventanaist.grid_columnconfigure(0, weight=1)
        ventanaist.grid_columnconfigure(1, weight=0)
        ventanaist.grid_columnconfigure(2, weight=1)

       
        ctk.CTkLabel(ventanaist, 
                    text="¡TRABAJADOR!",
                    font=("Open Sans", 50, "bold"),
                    text_color="white",
                    bg_color="#9FB3DF").grid(row=0, column=0, columnspan=3, pady=20)
        
        ctk.CTkLabel(ventanaist,
                    text="Ingresa tu información para iniciar sesión.",
                    font=("Open Sans", 20),
                    text_color="black",
                    bg_color="#9FB3DF",
                    wraplength=800).grid(row=1, column=0, columnspan=3, pady=10)

        etiquetas = ["Contacto:", "Contraseña:"]
        placeholders = ["Teléfono/email", "Contraseña"]

        entries = {}

        for i, (label_text, placeholder) in enumerate(zip(etiquetas, placeholders)):
            ctk.CTkLabel(ventanaist,
                        text=label_text,
                        font=("Open Sans", 18, "bold"),
                        text_color="black",
                        bg_color="#9FB3DF").grid(row=i+2, column=0, sticky="e", padx=40, pady=10)
            
            entry = ctk.CTkEntry(ventanaist, 
                                placeholder_text=placeholder, 
                                width=300)
            
            if "contraseña" in label_text.lower():
                entry.configure(show="•")  
                
            entry.grid(row=i+2, column=1, sticky="w", padx=5, pady=10)
            entries[label_text] = entry

        def verificar_datos():
            contacto = entries["Contacto:"].get()
            contraseña = entries["Contraseña:"].get()

            if not contacto or not contraseña: 
                messagebox.showerror("Error", "Ingresa contacto y contraseña.", parent=ventanaist)
                return
            
            usuario_dummy = Usuario("","","","","")
            usuario = usuario_dummy.iniciar_sesion(db, contacto, contraseña)

            if usuario and usuario["tipo"].lower() == "trabajador":
                messagebox.showinfo("Inicio de sesión", f'Bienvenido {usuario["nombre"]}!!', parent=ventanaist)
                ventanaist.destroy()
                
                inicio_trabajador(ventana, usuario)
            else:
                messagebox.showerror("Error", "Credenciales incorrectas o no eres trabajador.", parent=ventanaist)

        ctk.CTkButton(ventanaist,
                    text="Ingresar",
                    font=("Open Sans", 30, "bold"),
                    fg_color="#FFF1D5",
                    text_color="black",
                    width=200,
                    height=70,
                    command=verificar_datos).grid(row=len(etiquetas)+3, column=0, columnspan=3, pady=30)

        ventanaist.protocol("WM_DELETE_WINDOW", lambda: [ventanaist.destroy(), master.deiconify()])

    Inicio= tk.Label(ventana, text="Inicia sesión", font=("Open Sans", 60, "bold"), bg="#9FB3DF", fg="white")
    Inicio.grid(row=0, column=0, sticky="n", pady=40) 
  
    Empleador=ctk.CTkButton(master=ventana, text="Empleador", font=("Open Sans", 40, "bold"), bg_color="#9FB3DF", border_color="#FFF1D5", fg_color="#FFF1D5", text_color= "black",
                            width=300, height=100, command= lambda: inicio_sesion_empleador(ventana))
    Empleador.grid(row=1, column=0, sticky="n", pady=20)
          
    Trabajador=ctk.CTkButton(master=ventana, text="Trabajador", font=("Open Sans", 40, "bold"), bg_color="#9FB3DF", border_color="#FFF1D5", fg_color="#FFF1D5", text_color= "black",
                            width=300, height=100, command=lambda: inicio_sesion_trabajador(ventana))
    Trabajador.grid(row=2, column=0, sticky="n", pady=20)

    linea_frame = tk.Frame(ventana, bg="#9FB3DF")
    linea_frame.grid(row=3, column=0, sticky="n", pady=20)

    canvas_izq = tk.Canvas(linea_frame, width=200, height=3, bg="#9FB3DF", bd=0, highlightthickness=0)
    canvas_izq.create_line(0, 2, 200, 2, fill="#7d95c8", width=3)
    canvas_izq.pack(side="left", padx=10)

    o= tk.Label(linea_frame, text="o", font=("Open Sans", 40, "bold"), bg="#9FB3DF", fg="white")
    o.pack(side="left", padx=10)

    canvas_der = tk.Canvas(linea_frame, width=200, height=3, bg="#9FB3DF", bd=0, highlightthickness=0)
    canvas_der.create_line(0, 2, 200, 2, fill="#7d95c8", width=3)
    canvas_der.pack(side="left", padx=10)
    
    def inicio_registro():
        ventana.withdraw()
        ventana_registrarse(ventana)
    
    Registrarse=ctk.CTkButton(master=ventana, text="Registrarse", font=("Open Sans", 35, "bold"), bg_color="#9FB3DF", border_color="#FFF1D5", fg_color="#FFF1D5", text_color= "black",
                            width=300, height=70, command=inicio_registro)
    Registrarse.grid(row=4, column=0, sticky="n", pady=40)

    ventana.mainloop()

if __name__== "__main__":  
    Ventana_inicio()   

