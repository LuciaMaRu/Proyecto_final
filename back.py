import os
import csv
import shutil
from datetime import datetime
from uuid import uuid4
from typing import List, Dict, Optional
from werkzeug.utils import secure_filename  
from PIL import Image
import pandas as pd
from analisis import *
from graficos import *

# FOTOS
BASE_DIR= os.path.dirname(os.path.abspath(__file__))
FOTOS_PERFIL_DIR = os.path.join(BASE_DIR, "static","fotos_perfil")
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB
DEFAULT_PROFILE_PIC = os.path.join(BASE_DIR, "static","default_profile.png")
os.makedirs(FOTOS_PERFIL_DIR, exist_ok=True)

class Database:
    def __init__(self, base_filename: str):
        self.base_filename = base_filename
        self.tables = {
            'usuarios': f"{base_filename}_usuarios.csv",
            'trabajadores': f"{base_filename}_trabajadores.csv",
            'empleadores': f"{base_filename}_empleadores.csv",
            'servicios': f"{base_filename}_servicios.csv",
            'curriculums': f"{base_filename}_curriculums.csv",
            'contrataciones': f"{base_filename}_contrataciones.csv",
            'calificaciones': f"{base_filename}_calificaciones.csv",
            'notificaciones': f"{base_filename}_notificaciones.csv"
        }
        self.data = self._load_data()
    
    def _load_data(self) -> Dict:
        data = {}
        for table_name, filename in self.tables.items():
            data[table_name] = []
            try:
                with open(filename, mode='r', newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        converted_row = {}
                        for key, value in row.items():
                            if value.lower() == 'true':
                                converted_row[key] = True
                            elif value.lower() == 'false':
                                converted_row[key] = False
                            elif value.replace('.', '', 1).isdigit():
                                converted_row[key] = float(value) if '.' in value else int(value)
                            else:
                                converted_row[key] = value
                        data[table_name].append(converted_row)
            except FileNotFoundError:
                pass
        return data

    
    def save_data(self):
        success = True
        
        for table_name, records in self.data.items():
            if table_name not in self.tables:
                print(f"[ERROR] Tabla {table_name} no configurada")
                success = False
                continue
                
            filename = self.tables[table_name]
            fieldnames = set()
            for record in records:
                fieldnames.update(record.keys())
            fieldnames = list(fieldnames)
            
            try:
                # Crear backup
                if os.path.exists(filename):
                    shutil.copyfile(filename, filename + '.bak')
                
                # Escribir archivo temporal
                temp_file = filename + '.tmp'
                with open(temp_file, mode='w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(records)
                
                # Reemplazar archivo original
                os.replace(temp_file, filename)
                
            except Exception as e:
                print(f"[ERROR] Al guardar {filename}: {str(e)}")
                success = False
                if os.path.exists(filename + '.bak'):
                    os.replace(filename + '.bak', filename)
        
        return success
     

    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        
        for user in self.data['usuarios']:
            if user['ID'] == user_id:
                return user
        return None

    def update_user(self, user_id: str, new_data: Dict) -> bool:
        
        for i, user in enumerate(self.data['usuarios']):
            if user['ID'] == user_id:
                self.data['usuarios'][i].update(new_data)
                self.save_data()
                return True
        return False
    
    def get_empleador_by_id(self, empleador_id: str) -> Optional[Dict]:
       
        for empleador in self.data['empleadores']:
            if empleador['ID'] == empleador_id:
                return empleador
        return None

    def update_empleador(self, empleador_id: str, new_data: Dict) -> bool:
        
        for i, empleador in enumerate(self.data['empleadores']):
            if empleador['ID'] == empleador_id:
                self.data['empleadores'][i].update(new_data)
                self.save_data()
                return True
        return False
    def get_trabajador_by_id(self, trabajador_id: str) -> Optional[Dict]:
        trabajador_id_str = str(trabajador_id)
        for trabajador in self.data['trabajadores']:
            if str(trabajador['ID']) == trabajador_id_str:
                return trabajador
        return None

    def update_trabajador(self, trabajador_id: str, new_data: Dict) -> bool:
        trabajador_id_str = str(trabajador_id)
        for i, trabajador in enumerate(self.data['trabajadores']):
            if str(trabajador['ID']) == trabajador_id_str:
                
                str_data = {k: str(v) if v is not None else '' for k, v in new_data.items()}
                self.data['trabajadores'][i].update(str_data)
                self.save_data()
                return True
        return False
    def add_curriculum(self, curriculum_data: Dict) -> bool:
        if 'curriculums' not in self.data:
            self.data['curriculums'] = []
        
        if any(cv['ID_trabajador'] == curriculum_data['ID_trabajador'] 
               for cv in self.data['curriculums']):
            return False
            
        self.data['curriculums'].append(curriculum_data)
        return self.save_data()
    
    def update_curriculum(self, cv_id: str, new_data: Dict) -> bool:
        for i, cv in enumerate(self.data.get('curriculums', [])):
            if cv['ID_cv'] == cv_id:
                self.data['curriculums'][i].update(new_data)
                return self.save_data()
        return False


class Usuario:
    def __init__(self, ID: str, nombre: str, contacto: str, contraseña: str, tipo: str, foto: str = ""):
        self.ID = ID
        self.nombre = nombre
        self.contacto = contacto
        self.contraseña = contraseña
        self.tipo = tipo
        self.foto = foto
        
    @staticmethod
    def allowed_file(filename: str) -> bool:
        return ('.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS)
    
    @staticmethod
    def validate_image(file_stream) -> bool:
        try:
            file_stream.seek(0)
            Image.open(file_stream).verify()
            file_stream.seek(0)
            return True
        except Exception:
            return False
    
    def subir_foto(self, db: Database, file) -> bool:
        if not file or file.filename == '':
            return False
        if not self.allowed_file(file.filename):
            return False
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        if file_size > MAX_FILE_SIZE:
            return False
        if not self.validate_image(file.stream):
            return False
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{self.ID}_{uuid4().hex[:8]}.{ext}"
        filename = secure_filename(filename)
        file_path = os.path.join(FOTOS_PERFIL_DIR, filename)
        file.save(file_path)
        if self.foto and os.path.exists(os.path.join(FOTOS_PERFIL_DIR, self.foto)):
            try:
                os.remove(os.path.join(FOTOS_PERFIL_DIR, self.foto))
            except OSError:
                pass
        self.foto = filename
        for i, usuario in enumerate(db.data['usuarios']):
            if usuario['ID'] == self.ID:
                db.data['usuarios'][i]['foto'] = filename
                db.save_data()
                break
        return True
    
    def obtener_url_foto(self) -> str:
        if not self.foto:
            return DEFAULT_PROFILE_PIC
        return f"/{FOTOS_PERFIL_DIR}/{self.foto}"
        
    def reg_usuario(self, db: Database) -> bool:
        usuario_data = {
            'ID': self.ID,
            'nombre': self.nombre,
            'contacto': self.contacto,
            'contraseña': self.contraseña,
            'tipo': self.tipo,
            'foto': self.foto if self.foto else ""
        }
        
        for usuario in db.data['usuarios']:
            if usuario['contacto'] == self.contacto:
                return False
        db.data['usuarios'].append(usuario_data)
        db.save_data()
        return True
    
    def iniciar_sesion(self, db: Database, contacto: str, contraseña: str) -> Optional[Dict]:
        for usuario in db.data['usuarios']:
            if str(usuario['contacto']) == str(contacto) and str(usuario['contraseña']) == str(contraseña):
               
                if usuario['tipo'] == 'trabajador':
                    trabajador = next((t for t in db.data['trabajadores'] if t['ID'] == usuario['ID']), None)
                    if trabajador:
                        return {**usuario, **trabajador, 'tipo': 'trabajador'}
                elif usuario['tipo'] == 'empleador':
                    empleador = next((e for e in db.data['empleadores'] if e['ID'] == usuario['ID']), None)
                    if empleador:
                        return {**usuario, **empleador, 'tipo': 'empleador'}
        return None
    
    def editar_perfil(self, db: Database, **kwargs) -> bool:
        if 'foto' in kwargs:
            
            return False
            
        for i, usuario in enumerate(db.data['usuarios']):
            if usuario['ID'] == self.ID:
                for key, value in kwargs.items():
                    if key in usuario:
                        db.data['usuarios'][i][key] = value
                db.save_data()
                return True
        return False
    
    def eliminar_cuenta(self, db: Database) -> bool:
        if not hasattr(db, 'data') or 'usuarios' not in db.data:
            print("[ERROR] Estructura de datos inválida en la base de datos")
            return False

        eliminado_usuario = False
        eliminado_tabla_especifica = False
        tabla_especifica = 'empleadores' if self.tipo.lower() == 'empleador' else 'trabajadores'

        try:
            
            if self.foto:
                foto_path = os.path.join(FOTOS_PERFIL_DIR, self.foto)
                if os.path.exists(foto_path):
                    try:
                        os.remove(foto_path)
                        print(f"[DEBUG] Foto eliminada: {foto_path}")
                    except Exception as e:
                        print(f"[ERROR] No se pudo eliminar la foto: {str(e)}")

            
            for i, usuario in enumerate(db.data['usuarios'][:]):
                if usuario['ID'] == self.ID:
                    db.data['usuarios'].pop(i)
                    eliminado_usuario = True
                    print(f"[DEBUG] Usuario eliminado de tabla general: {self.ID}")

            
            if tabla_especifica in db.data:
                for i, item in enumerate(db.data[tabla_especifica][:]):
                    if item['ID'] == self.ID:
                        db.data[tabla_especifica].pop(i)
                        eliminado_tabla_especifica = True
                        print(f"[DEBUG] Usuario eliminado de {tabla_especifica}: {self.ID}")

            
            if eliminado_usuario or eliminado_tabla_especifica:
                try:
                    db.save_data()
                    print("[DEBUG] Datos guardados correctamente")
                    
                    
                    usuario_existe = any(u['ID'] == self.ID for u in db.data['usuarios'])
                    if usuario_existe:
                        print("[ERROR] El usuario sigue existiendo después de la eliminación")
                        return False
                    
                    return True
                except Exception as e:
                    print(f"[ERROR] No se pudo guardar los cambios: {str(e)}")
                    return False

            print("[WARNING] No se encontró el usuario para eliminar")
            return False

        except Exception as e:
            print(f"[ERROR] Error inesperado durante eliminación: {str(e)}")
            return False


class Trabajador(Usuario):
    def __init__(self, ID: str, nombre: str, contacto: str, contraseña: str, foto: str, profesion: str, experiencia_laboral: str, calificacion: float = 0.0, nivel: str = "principiante", disponibilidad: bool = True):
        super().__init__(ID, nombre, contacto, contraseña, "trabajador", foto)
        self.habilidades = []
        self.profesion = profesion
        self.experiencia_lab = experiencia_laboral
        self.calificacion = calificacion
        self.nivel = nivel
        self.disponibilidad = disponibilidad
        
    def reg_usuario(self, db: Database) -> bool:
        if super().reg_usuario(db):
            trabajador_data = {
                'ID': self.ID,
                'profesion': self.profesion,
                'experiencia_lab': self.experiencia_lab,
                'calificacion': self.calificacion,
                'nivel': self.nivel,
                'disponibilidad': self.disponibilidad,
                'habilidades': self.habilidades
            }
            db.data['trabajadores'].append(trabajador_data)
            db.save_data()
            return True
        return False
    
    def actualizar_hab(self, db: Database, nuevas_habilidades: List[str]) -> bool:
        for i, trabajador in enumerate(db.data['trabajadores']):
            if trabajador['ID'] == self.ID:
                db.data['trabajadores'][i]['habilidades'] = nuevas_habilidades
                db.save_data()
                self.habilidades = nuevas_habilidades
                return True
        return False
    
    def actualizar_dispo(self, db: Database, disponibilidad: bool) -> bool:
        for i, trabajador in enumerate(db.data['trabajadores']):
            if trabajador['ID'] == self.ID:
                db.data['trabajadores'][i]['disponibilidad'] = disponibilidad
                db.save_data()
                self.disponibilidad = disponibilidad
                return True
        return False
    
    def actualizar_portafolio(self, db: Database, portafolio: Dict) -> bool:
        for i, cv in enumerate(db.data['curriculums']):
            if cv['ID_trabajador'] == self.ID:
                db.data['curriculums'][i]['portafolio'] = portafolio
                db.data['curriculums'][i]['fecha_last_actualizacion'] = datetime.now().isoformat()
                db.save_data()
                return True
        
        nuevo_cv = {
            'ID_cv': str(uuid4()),
            'ID_trabajador': self.ID,
            'habilidades': self.habilidades,
            'profesion': self.profesion,
            'formacion_academica': "",
            'experiencia_profesional': self.experiencia_lab,
            'certificaciones': [],
            'idiomas': [],
            'portafolio': portafolio,
            'fecha_last_actualizacion': datetime.now().isoformat()
        }
        db.data['curriculums'].append(nuevo_cv)
        db.save_data()
        return True

class Empleador(Usuario):
    def __init__(self, ID: str, nombre: str, contacto: str, contraseña: str, foto: str, reputacion: float = 0.0, historial: List[str] = None, metodo_pago: str = "", nivel: str = "nuevo", calificacion: float = 0.0):
        super().__init__(ID, nombre, contacto, contraseña, "empleador", foto)
        self.reputacion = reputacion
        self.historial = historial if historial else []
        self.metodo_pago = metodo_pago
        self.nivel = nivel
        self.calificacion = calificacion
        
    def reg_usuario(self, db: Database) -> bool:
        if super().reg_usuario(db):
            empleador_data = {
                'ID': self.ID,
                'reputacion': self.reputacion,
                'historial': self.historial,
                'metodo_pago': self.metodo_pago,
                'nivel': self.nivel,
                'calificacion': self.calificacion
            }
            db.data['empleadores'].append(empleador_data)
            db.save_data()
            return True
        return False
    
    def buscar_trabajador(self, db: Database, habilidades: List[str] = None, profesion: str = None, nivel: str = None) -> List[Dict]:
        resultados = []
        
        for trabajador in db.data['trabajadores']:
            usuario = next((u for u in db.data['usuarios'] if u['ID'] == trabajador['ID']), None)
            if not usuario:
                continue
                
            match = True
            if habilidades and not all(h in trabajador['habilidades'] for h in habilidades):
                match = False
            if profesion and trabajador['profesion'].lower() != profesion.lower():
                match = False
            if nivel and trabajador['nivel'].lower() != nivel.lower():
                match = False
                
            if match:
                trabajador_data = {
                    **usuario,
                    **trabajador,
                    'cv': next((cv for cv in db.data['curriculums'] if cv['ID_trabajador'] == trabajador['ID']), None)
                }
                resultados.append(trabajador_data)
        return resultados
    
    def solicitar_trabajador(self, db: Database, ID_trabajador: str, ID_servicio: str) -> bool:
        servicio = next((s for s in db.data['servicios'] if s['ID_servicio'] == ID_servicio), None)
        trabajador = next((t for t in db.data['trabajadores'] if t['ID'] == ID_trabajador), None)
        
        if not servicio or not trabajador:
            return False
            
        notificacion = {
            'ID_notificacion': str(uuid4()),
            'ID_destinatario': ID_trabajador,
            'ID_emisor': self.ID,
            'mensaje': f"Tienes una nueva solicitud para el servicio: {servicio['nombre']}",
            'tipo_nots': 'solicitud_trabajo',
            'fecha_envio': datetime.now().isoformat(),
            'estado': 'no_leido',
            'ID_servicio': ID_servicio
        }
        
        db.data['notificaciones'].append(notificacion)
        db.save_data()
        return True
    
    def calificar_trabajador(self, db: Database, ID_trabajador: str, puntuacion: float, comentarios: str, ID_contratacion: str) -> bool:
        contratacion = next((c for c in db.data['contrataciones'] if c['ID_contratacion'] == ID_contratacion), None)
        if not contratacion or contratacion['ID_empleador'] != self.ID or contratacion['ID_trabajador'] != ID_trabajador:
            return False
        calificacion = {
            'ID_calificacion': str(uuid4()),
            'ID_evaluado': ID_trabajador,
            'ID_evaluador': self.ID,
            'puntuacion': puntuacion,
            'fecha': datetime.now().isoformat(),
            'comentarios': comentarios,
            'ID_contratacion': ID_contratacion
        }
        
        db.data['calificaciones'].append(calificacion)
        
        # Actualizar calificación promedio del trabajador
        calificaciones_trabajador = [c['puntuacion'] for c in db.data['calificaciones'] if c['ID_evaluado'] == ID_trabajador]
        nueva_calificacion = sum(calificaciones_trabajador) / len(calificaciones_trabajador)
        
        for i, trabajador in enumerate(db.data['trabajadores']):
            if trabajador['ID'] == ID_trabajador:
                db.data['trabajadores'][i]['calificacion'] = round(nueva_calificacion, 1)
                break
        db.save_data()
        return True

class Servicio:
    def __init__(self, ID_servicio: str, nombre: str, estado: str = "abierto", fecha_publicacion: str = None, ID_empleador: str = None, descripcion: str = "", habilidades_requeridas: List[str] = None):
        self.ID_servicio = ID_servicio
        self.nombre = nombre
        self.estado = estado
        self.fecha_publicacion = fecha_publicacion or datetime.now().isoformat()
        self.ID_empleador = ID_empleador
        self.descripcion = descripcion
        self.habilidades_requeridas = habilidades_requeridas if habilidades_requeridas else []
        
    def publicar_servicio(self, db: Database) -> bool:
        servicio_data = {
            'ID_servicio': self.ID_servicio,
            'nombre': self.nombre,
            'estado': self.estado,
            'fecha_publicacion': self.fecha_publicacion,
            'ID_empleador': self.ID_empleador,
            'descripcion': self.descripcion,
            'habilidades_requeridas': self.habilidades_requeridas
        }
        
        db.data['servicios'].append(servicio_data)
        db.save_data()
        return True
    
    def actualizar_servicio(self, db: Database, **kwargs) -> bool:
        for i, servicio in enumerate(db.data['servicios']):
            if servicio['ID_servicio'] == self.ID_servicio:
                for key, value in kwargs.items():
                    if key in servicio:
                        db.data['servicios'][i][key] = value
                db.save_data()
                return True
        return False
    
    def eliminar_servicio(self, db: Database) -> bool:
        for i, servicio in enumerate(db.data['servicios']):
            if servicio['ID_servicio'] == self.ID_servicio:
                db.data['servicios'].pop(i)
                db.save_data()
                return True
        return False
    
    @staticmethod
    def obtener_servicios(db: Database, ID_empleador: str = None, estado: str = None) -> List[Dict]:
        resultados = []
        for servicio in db.data['servicios']:
            match = True
            if ID_empleador and servicio['ID_empleador'] != ID_empleador:
                match = False
            if estado and servicio['estado'].lower() != estado.lower():
                match = False
                
            if match:
                empleador = next((e for e in db.data['empleadores'] if e['ID'] == servicio['ID_empleador']), None)
                usuario_empleador = next((u for u in db.data['usuarios'] if u['ID'] == servicio['ID_empleador']), None)
                
                servicio_data = {
                    **servicio,
                    'empleador': {
                        **usuario_empleador,
                        **empleador
                    } if empleador and usuario_empleador else None
                }
                resultados.append(servicio_data)
        return resultados

class Curriculum:
    def __init__(self, ID_cv: str, ID_trabajador: str, habilidades: List[str], profesion: str, formacion_academica: str, experiencia_profesional: str, certificaciones: List[str], idiomas: List[str], portafolio: Dict, fecha_last_actualizacion: str):
        self.ID_cv = ID_cv
        self.ID_trabajador = ID_trabajador
        self.habilidades = habilidades
        self.profesion = profesion
        self.formacion_academica = formacion_academica
        self.experiencia_profesional = experiencia_profesional
        self.certificaciones = certificaciones
        self.idiomas = idiomas
        self.portafolio = portafolio
        self.fecha_last_actualizacion = fecha_last_actualizacion
        
    #Actualizar curriculum
    def actualizar_datos(self, db: Database, **kwargs) -> bool:
        for i, cv in enumerate(db.data['curriculums']):
            if cv['ID_cv'] == self.ID_cv:
                for key, value in kwargs.items():
                    if key in cv:
                        db.data['curriculums'][i][key] = value
                db.data['curriculums'][i]['fecha_last_actualizacion'] = datetime.now().isoformat()
                db.save_data()
                return True
        return False
    
    @staticmethod
    def mostrar_cv_completo(db: Database, ID_trabajador: str) -> Optional[Dict]:
        cv = next((c for c in db.data['curriculums'] if c['ID_trabajador'] == ID_trabajador), None)
        if not cv:
            return None
            
        trabajador = next((t for t in db.data['trabajadores'] if t['ID'] == ID_trabajador), None)
        usuario = next((u for u in db.data['usuarios'] if u['ID'] == ID_trabajador), None)
        calificaciones = [c for c in db.data['calificaciones'] if c['ID_evaluado'] == ID_trabajador]
        cv_completo = {
            **cv,
            'trabajador': {
                **usuario,
                **trabajador
            },
            'calificaciones': calificaciones
        }
        
        return cv_completo

class Contratacion:
    def __init__(self, ID_contratacion: str, ID_empleador: str, ID_trabajador: str, fecha_inicio: str, estado_contratacion: str, modalidad: str, valor_acordado: float, ID_servicio: str = None):
        self.ID_contratacion = ID_contratacion
        self.ID_empleador = ID_empleador
        self.ID_trabajador = ID_trabajador
        self.fecha_inicio = fecha_inicio
        self.estado_contratacion = estado_contratacion
        self.modalidad = modalidad
        self.valor_acordado = valor_acordado
        self.ID_servicio = ID_servicio
        
    def registrar_contratacion(self, db: Database) -> bool:
        contratacion_data = {
            'ID_contratacion': self.ID_contratacion,
            'ID_empleador': self.ID_empleador,
            'ID_trabajador': self.ID_trabajador,
            'fecha_inicio': self.fecha_inicio,
            'estado_contratacion': self.estado_contratacion,
            'modalidad': self.modalidad,
            'valor_acordado': self.valor_acordado,
            'ID_servicio': self.ID_servicio
        }
        
        db.data['contrataciones'].append(contratacion_data)
        
        # Actualizar estado del servicio si existe
        if self.ID_servicio:
            for i, servicio in enumerate(db.data['servicios']):
                if servicio['ID_servicio'] == self.ID_servicio:
                    db.data['servicios'][i]['estado'] = "en_proceso"
                    break
        db.save_data()
        return True
    
    def finalizar_contratacion(self, db: Database) -> bool:
        for i, contratacion in enumerate(db.data['contrataciones']):
            if contratacion['ID_contratacion'] == self.ID_contratacion:
                db.data['contrataciones'][i]['estado_contratacion'] = "finalizada"
                
                # Actualizar estado del servicio si existe
                if self.ID_servicio:
                    for j, servicio in enumerate(db.data['servicios']):
                        if servicio['ID_servicio'] == self.ID_servicio:
                            db.data['servicios'][j]['estado'] = "cerrado"
                            break
                db.save_data()
                return True
        return False
    
    @staticmethod
    def obtener_contrataciones(db: Database, ID_usuario: str = None, tipo_usuario: str = None, estado: str = None) -> List[Dict]:
        resultados = []
        
        for contratacion in db.data['contrataciones']:
            match = True
            if ID_usuario and tipo_usuario == 'empleador' and contratacion['ID_empleador'] != ID_usuario:
                match = False
            if ID_usuario and tipo_usuario == 'trabajador' and contratacion['ID_trabajador'] != ID_usuario:
                match = False
            if estado and contratacion['estado_contratacion'].lower() != estado.lower():
                match = False
            if match:
                empleador = next((e for e in db.data['empleadores'] if e['ID'] == contratacion['ID_empleador']), None)
                usuario_empleador = next((u for u in db.data['usuarios'] if u['ID'] == contratacion['ID_empleador']), None)
                trabajador = next((t for t in db.data['trabajadores'] if t['ID'] == contratacion['ID_trabajador']), None)
                usuario_trabajador = next((u for u in db.data['usuarios'] if u['ID'] == contratacion['ID_trabajador']), None)
                servicio = next((s for s in db.data['servicios'] if s['ID_servicio'] == contratacion.get('ID_servicio')), None)
                contratacion_data = {
                    **contratacion,
                    'empleador': {
                        **usuario_empleador,
                        **empleador
                    } if empleador and usuario_empleador else None,
                    'trabajador': {
                        **usuario_trabajador,
                        **trabajador
                    } if trabajador and usuario_trabajador else None,
                    'servicio': servicio
                }
                resultados.append(contratacion_data)
        return resultados
    @staticmethod
    def actualizar_estado(db, ID_contratacion, nuevo_estado):
        """Actualiza el estado de una contratación por su ID"""
        actualizada = False
        for c in db['contrataciones']:
            if c['ID_contratacion'] == ID_contratacion:
                c['estado_contratacion'] = nuevo_estado
                actualizada = True
                break
        if actualizada:
            db.guardar()
        return actualizada

class Calificacion:
    def __init__(self, ID_calificacion: str, ID_evaluado: str, ID_evaluador: str, puntuacion: float, fecha: str, comentarios: str, ID_contratacion: str):
        self.ID_calificacion = ID_calificacion
        self.ID_evaluado = ID_evaluado
        self.ID_evaluador = ID_evaluador
        self.puntuacion = puntuacion
        self.fecha = fecha
        self.comentarios = comentarios
        self.ID_contratacion = ID_contratacion
        
    def dejar_calificacion(self, db: Database) -> bool:
        calificacion_data = {
            'ID_calificacion': self.ID_calificacion,
            'ID_evaluado': self.ID_evaluado,
            'ID_evaluador': self.ID_evaluador,
            'puntuacion': self.puntuacion,
            'fecha': self.fecha,
            'comentarios': self.comentarios,
            'ID_contratacion': self.ID_contratacion
        }
        db.data['calificaciones'].append(calificacion_data)
        db.save_data()
        return True
    
    @staticmethod
    def ver_calificacion(db: Database, ID_evaluado: str) -> List[Dict]:
        return [c for c in db.data['calificaciones'] if c['ID_evaluado'] == ID_evaluado]
    
    @staticmethod
    def historial_calif(db: Database, ID_evaluador: str) -> List[Dict]:
        return [c for c in db.data['calificaciones'] if c['ID_evaluador'] == ID_evaluador]

class Notificaciones:
    def __init__(self, ID_notificacion: str, ID_usuario: str, mensaje: str, tipo: str, fecha: str, leida: str, ID_contratacion: str = None):
        self.ID_notificacion = ID_notificacion
        self.ID_usuario = ID_usuario 
        self.mensaje = mensaje
        self.tipo = tipo
        self.fecha = fecha
        self.leida = leida
        self.ID_contratacion = ID_contratacion
        
    def enviar_nots(self, db: Database) -> bool:
        notificacion_data = {
            'ID_notificacion': self.ID_notificacion,
            'ID_usuario': self.ID_usuario,
            'mensaje': self.mensaje,
            'tipo': self.tipo,
            'fecha': self.fecha,
            'leida': self.leida,
            'ID_contratacion': self.ID_contratacion
        }
        db.data['notificaciones'].append(notificacion_data)
        db.save_data()
        return True

    @staticmethod
    def marcar_leido(db: Database, ID_notificacion: str) -> bool:
        for i, notificacion in enumerate(db.data['notificaciones']):
            if notificacion['ID_notificacion'] == ID_notificacion:
                db.data['notificaciones'][i]['leida'] = "True"  # O el valor que uses para leído
                db.save_data()
                return True
        return False
    
    @staticmethod
    def historial_nots(db: Database, ID_usuario: str, leida: bool = None) -> list:
        resultados = []
        for notificacion in db.data['notificaciones']:
            if notificacion['ID_usuario'] == ID_usuario:
                # Si filtro está definido y no coincide, salto
                if leida is not None and notificacion['leida'] != leida:
                    continue
                resultados.append(notificacion)
        return sorted(resultados, key=lambda x: x['fecha'], reverse=True)
    
class Estadistica:
    def __init__(self, db):
        self.db = db
        try:
            self.df_trabajadores = self._crear_df_trabajadores()
            self.df_servicios = self._crear_df_servicios()
            self.df_contrataciones = self._crear_df_contrataciones()
        except Exception as e:
            raise ValueError(f"Error al cargar datos: {str(e)}")

    def _crear_df_trabajadores(self):
        if 'trabajadores' not in self.db.data:
            raise ValueError("No existe la tabla 'trabajadores' en la base de datos")
            
        df = pd.DataFrame(self.db.data['trabajadores'])
        
        # Verificar y estandarizar habilidades
        if 'habilidades' not in df.columns:
            df['habilidades'] = [[] for _ in range(len(df))]
        else:
            df['habilidades'] = df['habilidades'].apply(
                lambda x: x if isinstance(x, list) else [x] if pd.notna(x) else []
            )
        return df

    def _crear_df_servicios(self):
        if 'servicios' not in self.db.data:
            raise ValueError("No existe la tabla 'servicios' en la base de datos")
            
        df = pd.DataFrame(self.db.data['servicios'])
        
        # Verificar y estandarizar habilidades requeridas
        if 'habilidades_requeridas' not in df.columns:
            df['habilidades_requeridas'] = [[] for _ in range(len(df))]
        else:
            df['habilidades_requeridas'] = df['habilidades_requeridas'].apply(
                lambda x: x if isinstance(x, list) else [x] if pd.notna(x) else []
            )
        return df

    def _crear_df_contrataciones(self):
        if 'contrataciones' not in self.db.data:
            return pd.DataFrame()  # Retorna dataframe vacío si no existe
            
        df = pd.DataFrame(self.db.data['contrataciones'])
        
        # Verificar fechas
        if 'fecha_inicio' in df.columns:
            df['fecha_contratacion'] = pd.to_datetime(df['fecha_inicio'], errors='coerce')
        return df

    def graficar_habilidades_mas_demandadas(self, top_n=10):
        """Devuelve figura de matplotlib con habilidades demandadas"""
        try:
            if self.df_servicios.empty or 'habilidades_requeridas' not in self.df_servicios.columns:
                return self._crear_figura_vacia("No hay datos de habilidades requeridas")
                
            habilidades = self.df_servicios.explode('habilidades_requeridas')
            conteo = habilidades['habilidades_requeridas'].value_counts().head(top_n)
            
            fig, ax = plt.subplots(figsize=(10, 6))
            conteo.plot(kind='barh', ax=ax, color='skyblue')
            ax.set_title(f'Top {top_n} Habilidades Más Demandadas')
            ax.set_xlabel('Número de Servicios')
            ax.invert_yaxis()
            plt.tight_layout()
            return fig
            
        except Exception as e:
            print(f"Error al graficar: {str(e)}")
            return self._crear_figura_vacia("Error al generar gráfica")

    def graficar_habilidades_mas_ofrecidas(self, top_n=10):
        """Devuelve figura de matplotlib con habilidades ofrecidas"""
        try:
            if self.df_trabajadores.empty or 'habilidades' not in self.df_trabajadores.columns:
                return self._crear_figura_vacia("No hay datos de habilidades ofrecidas")
                
            habilidades = self.df_trabajadores.explode('habilidades')
            conteo = habilidades['habilidades'].value_counts().head(top_n)
            
            fig, ax = plt.subplots(figsize=(10, 6))
            conteo.plot(kind='barh', ax=ax, color='lightgreen')
            ax.set_title(f'Top {top_n} Habilidades Más Ofrecidas')
            ax.set_xlabel('Número de Trabajadores')
            ax.invert_yaxis()
            plt.tight_layout()
            return fig
            
        except Exception as e:
            print(f"Error al graficar: {str(e)}")
            return self._crear_figura_vacia("Error al generar gráfica")

    def _crear_figura_vacia(self, mensaje):
        """Crea una figura con mensaje cuando no hay datos"""
        fig, ax = plt.subplots(figsize=(10, 2))
        ax.text(0.5, 0.5, mensaje, 
                ha='center', va='center', 
                fontsize=12, color='gray')
        ax.axis('off')
        return fig

    def graficar_habilidades_mas_ofrecidas(self, top_n=10):
        """Habilidades más comunes entre trabajadores"""
        habilidades = self.df_trabajadores.explode('habilidades')
        conteo = habilidades['habilidades'].value_counts().head(top_n)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        conteo.plot(kind='barh', ax=ax, color='lightgreen')
        ax.set_title(f'Top {top_n} Habilidades Más Ofrecidas')
        ax.set_xlabel('Número de Trabajadores que la ofrecen')
        ax.invert_yaxis()
        plt.tight_layout()
        return fig

    def graficar_brecha_demanda_oferta(self, top_n=10):
        """Diferencia entre demanda y oferta de habilidades"""
        demanda = self.df_servicios.explode('habilidades_requeridas')['habilidades_requeridas'].value_counts()
        oferta = self.df_trabajadores.explode('habilidades')['habilidades'].value_counts()
        
        brecha = demanda.sub(oferta, fill_value=0).sort_values(ascending=False)
        top_brecha = brecha.head(top_n)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        top_brecha.plot(kind='barh', ax=ax, color='salmon')
        ax.set_title(f'Top {top_n} Brechas Demanda-Oferta')
        ax.set_xlabel('Demanda - Oferta')
        ax.invert_yaxis()
        plt.tight_layout()
        return fig

    def graficar_servicios_por_mes(self):
        """Evolución temporal de servicios creados"""
        if 'fecha_creacion' not in self.df_servicios.columns:
            return None
            
        df = self.df_servicios.copy()
        df['fecha'] = pd.to_datetime(df['fecha_creacion'])
        df['mes'] = df['fecha'].dt.to_period('M')
        conteo = df['mes'].value_counts().sort_index()
        
        fig, ax = plt.subplots(figsize=(10, 5))
        conteo.plot(kind='line', ax=ax, marker='o', color='blue')
        ax.set_title('Servicios Creados por Mes')
        ax.set_xlabel('Mes')
        ax.set_ylabel('Número de Servicios')
        plt.xticks(rotation=45)
        plt.tight_layout()
        return fig

    def graficar_contrataciones_por_mes(self):
        """Evolución temporal de contrataciones"""
        if self.df_contrataciones.empty or 'fecha_contratacion' not in self.df_contrataciones.columns:
            return None
            
        df = self.df_contrataciones.copy()
        df['mes'] = df['fecha_contratacion'].dt.to_period('M')
        conteo = df['mes'].value_counts().sort_index()
        
        fig, ax = plt.subplots(figsize=(10, 5))
        conteo.plot(kind='bar', ax=ax, color='purple')
        ax.set_title('Contrataciones por Mes')
        ax.set_xlabel('Mes')
        ax.set_ylabel('Número de Contrataciones')
        plt.xticks(rotation=45)
        plt.tight_layout()
        return fig

    def consultar_analisis_DemandaOferta(self):
        
        demanda = self.df_servicios.explode('habilidades_requeridas')['habilidades_requeridas'].value_counts()
        oferta = self.df_trabajadores.explode('habilidades')['habilidades'].value_counts()
        
        brecha = demanda.sub(oferta, fill_value=0)
        brecha_positiva = brecha[brecha > 0].sort_values(ascending=False)
        
        recomendaciones = [
            f"Habilidad '{hab}' tiene alta demanda ({int(diff)} más que oferta)"
            for hab, diff in brecha_positiva.head(5).items()
        ]
        
        if not recomendaciones:
            recomendaciones = ["No se detectaron brechas significativas"]
            
        return recomendaciones
        
class Recomendaciones:
    def __init__(self, db):
        self.db = db
        self.df_trabajadores = self._crear_df_trabajadores()
        self.df_servicios = self._crear_df_servicios()

    def _crear_df_trabajadores(self):
        df = pd.DataFrame(self.db.data['trabajadores'])
        df['habilidades_ofrecidas'] = df['habilidades'].apply(lambda x: ",".join(x) if isinstance(x, list) else "")
        return df

    def _crear_df_servicios(self):
        df = pd.DataFrame(self.db.data['servicios'])
        df['habilidades_requeridas'] = df['habilidades_requeridas'].apply(lambda x: ",".join(x) if isinstance(x, list) else "")
        return df

    def consultar_tendencias(self, top_n=10):
        tendencias = recomendar_habilidades(self.df_servicios, self.df_trabajadores, top_n=top_n)
        return tendencias

    def enviar_notificaciones(self, top_n=5):
        tendencias = self.consultar_tendencias(top_n)
        habilidades_tendencia = set(tendencias['habilidad'].tolist())

        for trabajador in self.db.data['trabajadores']:
            ID_trabajador = trabajador['ID']
            habilidades_actuales = set(trabajador.get('habilidades', []))
            sugerencias = habilidades_tendencia - habilidades_actuales

            if sugerencias:
                mensaje = f"¡Nuevas habilidades en tendencia! Considera aprender: {', '.join(sugerencias)}"
                notificacion = Notificaciones(
                    ID_notificacion=generar_id(),
                    ID_destinatario=ID_trabajador,
                    ID_emisor="sistema",
                    mensaje=mensaje,
                    tipo_nots="recomendacion",
                    fecha_envio=obtener_fecha_actual(),
                    estado="no_leido"
                )
                notificacion.enviar_nots(self.db)

# Funciones de utilidad
def generar_id() -> str:
    return str(uuid4())

def obtener_fecha_actual() -> str:
    return datetime.now().isoformat()