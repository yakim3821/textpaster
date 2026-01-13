#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TextPaster - Программа для быстрого доступа к шаблонам текста
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import threading
import pyperclip
from pynput import keyboard
from pynput.keyboard import Key, KeyCode, Listener
import time
from collections import OrderedDict

class ConfigManager:
    """Менеджер конфигурации приложения (горячие клавиши и т.д.)"""
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = {
            "hotkeys": {
                "search_templates": "<ctrl>+1",
                "cascading_menu": "<ctrl>+2"
            },
            "features": {
                "auto_paste": False
            }
        }
        self.load_config()
    
    def load_config(self):
        """Загрузить конфигурацию из файла"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Объединить с дефолтной конфигурацией
                    self.config.update(loaded_config)
            except Exception as e:
                print(f"Ошибка загрузки конфигурации: {e}")
                self.save_config()
        else:
            self.save_config()
    
    def save_config(self):
        """Сохранить конфигурацию в файл"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")
    
    def get_hotkey(self, hotkey_name):
        """Получить горячую клавишу по названию"""
        return self.config.get("hotkeys", {}).get(hotkey_name, "")
    
    def set_hotkey(self, hotkey_name, hotkey_value):
        """Установить горячую клавишу"""
        if "hotkeys" not in self.config:
            self.config["hotkeys"] = {}
        self.config["hotkeys"][hotkey_name] = hotkey_value
        self.save_config()

    def get_feature(self, feature_name, default=False):
        """Получить значение фичи из конфигурации"""
        return self.config.get("features", {}).get(feature_name, default)

    def set_feature(self, feature_name, feature_value):
        """Установить значение фичи в конфигурации"""
        if "features" not in self.config:
            self.config["features"] = {}
        self.config["features"][feature_name] = bool(feature_value)
        self.save_config()

class TemplateNode:
    """Узел для хранения шаблона или папки"""
    def __init__(self, name, content="", is_folder=False):
        self.name = name
        self.content = content
        self.is_folder = is_folder
        self.children = OrderedDict()  # Использовать OrderedDict для сохранения порядка
        self.parent = None
    
    def add_child(self, child):
        """Добавить дочерний элемент"""
        child.parent = self
        self.children[child.name] = child
    
    def remove_child(self, name):
        """Удалить дочерний элемент"""
        if name in self.children:
            del self.children[name]
    
    def move_child_up(self, name):
        """Переместить дочерний элемент вверх в списке"""
        if name not in self.children:
            return False
        
        keys = list(self.children.keys())
        index = keys.index(name)
        
        if index > 0:
            # Переместить элемент вверх
            old_index = index
            new_index = index - 1
            
            # Создать новый упорядоченный словарь с измененным порядком
            new_children = OrderedDict()
            for i, key in enumerate(keys):
                if i == new_index:
                    new_children[keys[old_index]] = self.children[keys[old_index]]
                if i != old_index:
                    new_children[key] = self.children[key]
            
            self.children = new_children
            return True
        return False
    
    def move_child_down(self, name):
        """Переместить дочерний элемент вниз в списке"""
        if name not in self.children:
            return False
        
        keys = list(self.children.keys())
        index = keys.index(name)
        
        if index < len(keys) - 1:
            # Переместить элемент вниз
            old_index = index
            new_index = index + 1
            
            # Создать новый упорядоченный словарь с измененным порядком
            new_children = OrderedDict()
            for i, key in enumerate(keys):
                if i == old_index:
                    new_children[keys[new_index]] = self.children[keys[new_index]]
                elif i == new_index:
                    new_children[keys[old_index]] = self.children[keys[old_index]]
                else:
                    new_children[key] = self.children[key]
            
            self.children = new_children
            return True
        return False
    
    def get_path(self):
        """Получить полный путь до узла"""
        path = []
        current = self
        while current.parent is not None:
            path.append(current.name)
            current = current.parent
        return "/".join(reversed(path))

class TemplateManager:
    """Менеджер шаблонов"""
    def __init__(self, data_file="templates.json"):
        self.data_file = data_file
        self.root = TemplateNode("Root", "", True)
        self.load_templates()
    
    def save_templates(self):
        """Сохранить шаблоны в файл"""
        data = self._node_to_dict(self.root)
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_templates(self):
        """Загрузить шаблоны из файла"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.root = self._dict_to_node(data)
            except Exception as e:
                print(f"Ошибка загрузки шаблонов: {e}")
                self._create_sample_templates()
        else:
            self._create_sample_templates()
    
    def _create_sample_templates(self):
        """Создать примеры шаблонов"""
        # Папка приветствий
        greetings = TemplateNode("Приветствия", "", True)
        greetings.add_child(TemplateNode("Доброе утро", "Доброе утро! Как дела?"))
        greetings.add_child(TemplateNode("Добрый день", "Добрый день! Надеюсь, у вас все хорошо."))
        greetings.add_child(TemplateNode("Добрый вечер", "Добрый вечер! Хорошего отдыха."))
        self.root.add_child(greetings)
        
        # Папка подписей
        signatures = TemplateNode("Подписи", "", True)
        signatures.add_child(TemplateNode("Официальная", "С уважением,\nИван Иванов\nТел: +7-123-456-7890"))
        signatures.add_child(TemplateNode("Дружественная", "Всего наилучшего!\nИван"))
        self.root.add_child(signatures)
        
        # Папка программирования
        programming = TemplateNode("Программирование", "", True)
        python_folder = TemplateNode("Python", "", True)
        python_folder.add_child(TemplateNode("Импорты", "import os\nimport sys\nimport json"))
        python_folder.add_child(TemplateNode("Main функция", "if __name__ == '__main__':\n    main()"))
        programming.add_child(python_folder)
        self.root.add_child(programming)
        
        self.save_templates()
    
    def _node_to_dict(self, node):
        """Преобразовать узел в словарь с сохранением порядка"""
        data = {
            'name': node.name,
            'content': node.content,
            'is_folder': node.is_folder,
            'children': {}
        }
        # Сохранить порядок детей используя OrderedDict
        for child_name, child_node in node.children.items():
            data['children'][child_name] = self._node_to_dict(child_node)
        return data
    
    def _dict_to_node(self, data):
        """Преобразовать словарь в узел"""
        node = TemplateNode(data['name'], data.get('content', ''), data.get('is_folder', False))
        # Использовать OrderedDict для сохранения порядка при загрузке
        children_data = data.get('children', {})
        # Если это обычный dict, преобразуем в OrderedDict
        if children_data:
            for child_name in children_data:
                child_data = children_data[child_name]
                child = self._dict_to_node(child_data)
                node.add_child(child)
        return node

    def get_node_by_path(self, path):
        """Найти узел по пути вида 'Папка/Подпапка/Шаблон'"""
        if not path:
            return self.root

        parts = [p for p in path.split('/') if p]
        current = self.root
        for part in parts:
            if part in current.children:
                current = current.children[part]
            else:
                return None
        return current
    
    def search_templates(self, query, node=None):
        """Поиск шаблонов по названию"""
        if node is None:
            node = self.root
        
        results = []
        for child in node.children.values():
            if query.lower() in child.name.lower():
                results.append(child)
            if child.is_folder:
                results.extend(self.search_templates(query, child))
        
        return results

class CascadingMenuSelector:
    """Каскадное меню для выбора шаблонов (похоже на контекстное меню Windows)"""
    def __init__(self, template_manager, callback, root_window):
        self.template_manager = template_manager
        self.callback = callback
        self.root_window = root_window
        self.menus = {}  # Кэш меню для предотвращения дублей
        self.current_menu = None  # Текущее активное меню
        self._grab_win = None  # Прозрачное окно для перехвата кликов
    
    def show(self, event=None):
        """Показать главное меню с папками и шаблонами"""
        # Если меню уже открыто, закрыть его
        if self.current_menu is not None:
            self._on_escape_key()

        main_menu = tk.Menu(self.root_window, tearoff=0)
        self._build_menu(main_menu, self.template_manager.root)
        self.current_menu = main_menu

        # Получаем координаты для показа меню
        try:
            x = self.root_window.winfo_pointerx()
            y = self.root_window.winfo_pointery()
        except Exception:
            x = self.root_window.winfo_screenwidth() // 2
            y = self.root_window.winfo_screenheight() // 2

        # Создаем прозрачное окно на весь экран для перехвата кликов
        self._grab_win = tk.Toplevel(self.root_window)
        self._grab_win.overrideredirect(True)
        self._grab_win.attributes("-topmost", True)
        
        # Делаем окно невидимым - очень низкое значение alpha
        try:
            self._grab_win.attributes("-alpha", 0.00001)
        except Exception:
            pass
        
        # Устанавливаем размер на весь экран
        self._grab_win.geometry(
            f"{self.root_window.winfo_screenwidth()}x{self.root_window.winfo_screenheight()}+0+0"
        )

        # Привязываем клики и клавишу Escape к закрытию меню
        self._grab_win.bind("<ButtonPress>", self._on_mouse_click, add=True)
        self._grab_win.bind("<Escape>", self._on_escape_key, add=True)
        self._grab_win.focus_set()

        # Устанавливаем global grab для перехвата событий везде
        try:
            self._grab_win.grab_set_global()
        except Exception:
            # Fallback для некоторых систем
            self._grab_win.grab_set()

        # Показываем меню
        main_menu.post(x, y)
    
    def _build_menu(self, parent_menu, node):
        """Рекурсивно построить меню с подменю для папок"""
        # Сортируем дочерние элементы: папки первыми
        folders = []
        templates = []
        
        for child in node.children.values():
            if child.is_folder:
                folders.append(child)
            else:
                templates.append(child)
        
        # Добавляем папки с подменю
        for folder in sorted(folders, key=lambda x: x.name.lower()):
            submenu = tk.Menu(parent_menu, tearoff=0)
            self._build_menu(submenu, folder)
            parent_menu.add_cascade(label=f"📁 {folder.name}", menu=submenu)
        
        # Добавляем шаблоны как команды
        if folders:  # Разделитель между папками и шаблонами
            parent_menu.add_separator()
        
        for template in sorted(templates, key=lambda x: x.name.lower()):
            parent_menu.add_command(
                label=f"📄 {template.name}",
                command=lambda t=template: self._select_template(t)
            )
    
    def _on_escape_key(self, event=None):
        """Закрыть меню при нажатии Escape"""
        if self.current_menu is not None:
            try:
                self.current_menu.unpost()
            except:
                pass
        self._cleanup_menu_handlers()
    
    def _on_mouse_click(self, event):
        """Закрыть меню при клике вне его области"""
        if self.current_menu is not None:
            try:
                self.current_menu.unpost()
            except:
                pass
        self._cleanup_menu_handlers()
    
    def _cleanup_menu_handlers(self):
        """Очистить обработчики событий меню"""
        self.current_menu = None

        if self._grab_win is not None:
            try:
                self._grab_win.grab_release()
            except Exception:
                pass
            try:
                self._grab_win.destroy()
            except Exception:
                pass
            self._grab_win = None
    
    def _select_template(self, template):
        """Выбрать и скопировать шаблон"""
        # Закрываем меню и очищаем обработчики
        self._cleanup_menu_handlers()
        
        # Вызываем callback
        self.callback(template, source="cascading_menu")

class TextPasterApp:
    """Основное приложение TextPaster"""
    def __init__(self):
        self.config_manager = ConfigManager()
        self.template_manager = TemplateManager()
        self.popup_window = None
        self.hotkey_listener = None
        self.main_window = tk.Tk()
        self.cascading_menu = None
        self.init_main_window()
        self.cascading_menu = CascadingMenuSelector(self.template_manager, self.on_template_selected, self.main_window)
        self.init_hotkeys()
        self.hotkeys_handle = None  # Для хранения объекта GlobalHotKeys
    
    def init_main_window(self):
        """Инициализация основного окна"""
        self.main_window.title("TextPaster - Управление шаблонами")
        self.main_window.geometry("1050x700")
        
        # Меню
        menubar = tk.Menu(self.main_window)
        self.main_window.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Создать папку", command=self.create_folder)
        file_menu.add_command(label="Создать шаблон", command=self.create_template)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.main_window.quit)
        
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Правка", menu=edit_menu)
        edit_menu.add_command(label="Редактировать", command=self.edit_selected)
        edit_menu.add_command(label="Удалить", command=self.delete_selected)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="Горячие клавиши", command=self.show_hotkeys)
        
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Настройки", menu=settings_menu)
        settings_menu.add_command(label="Переназначить горячие клавиши", command=self.show_hotkey_settings)
        self.auto_paste_var = tk.BooleanVar(value=self.config_manager.get_feature("auto_paste", False))
        settings_menu.add_checkbutton(
            label="Быстрая вставка после выбора",
            variable=self.auto_paste_var,
            command=self.toggle_auto_paste
        )
        
        # Панель инструментов
        toolbar = ttk.Frame(self.main_window)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="Создать папку", command=self.create_folder).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Создать шаблон", command=self.create_template).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Редактировать", command=self.edit_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Удалить", command=self.delete_selected).pack(side=tk.LEFT, padx=2)
        
        # Разделитель
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        ttk.Button(toolbar, text="▲ Выше", command=self.move_selected_up).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="▼ Ниже", command=self.move_selected_down).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="↪ В папку", command=self.move_selected_to_folder).pack(side=tk.LEFT, padx=2)
        
        # Разделитель
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        ttk.Button(toolbar, text="🔍 Поиск шаблонов", command=self.show_popup_selector).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Меню выбора", command=lambda: self.cascading_menu.show() if self.cascading_menu else None).pack(side=tk.LEFT, padx=2)
        
        # Поиск
        search_frame = ttk.Frame(self.main_window)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', self.on_search)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Основной фрейм
        main_frame = ttk.Frame(self.main_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Дерево шаблонов
        self.tree = ttk.Treeview(main_frame, selectmode='extended')
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Скроллбар для дерева
        tree_scroll = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        tree_scroll.pack(side=tk.LEFT, fill=tk.Y)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        # Панель предпросмотра
        preview_frame = ttk.LabelFrame(main_frame, text="Предпросмотр")
        preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        
        self.preview_text = tk.Text(preview_frame, width=30, height=20, wrap=tk.WORD)
        self.preview_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Скроллбар для предпросмотра
        preview_scroll = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.preview_text.yview)
        preview_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.preview_text.configure(yscrollcommand=preview_scroll.set)
        
        # Привязка событий
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        self.tree.bind('<Double-1>', self.on_tree_double_click)
        self.tree.bind('<Button-3>', self.on_tree_right_click)
        
        # Горячие клавиши в главном окне
        self.main_window.bind('<Control-1>', lambda e: self.show_popup_selector())
        self.main_window.bind('<Control-2>', lambda e: self.cascading_menu.show())
        self.main_window.bind('<F2>', lambda e: self.edit_selected())
        self.main_window.bind('<Delete>', lambda e: self.delete_selected())
        self.main_window.bind('<Return>', lambda e: self.copy_to_clipboard())
        self.main_window.bind('<Control-f>', lambda e: search_entry.focus_set())
        
        # Контекстное меню
        self.context_menu = tk.Menu(self.main_window, tearoff=0)
        self.context_menu.add_command(label="Создать папку", command=self.create_folder)
        self.context_menu.add_command(label="Создать шаблон", command=self.create_template)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Редактировать", command=self.edit_selected)
        self.context_menu.add_command(label="Удалить", command=self.delete_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Копировать в буфер", command=self.copy_to_clipboard)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="▲ Переместить выше", command=self.move_selected_up)
        self.context_menu.add_command(label="▼ Переместить ниже", command=self.move_selected_down)
        self.context_menu.add_command(label="↪ Переместить в папку", command=self.move_selected_to_folder)
        
        self.refresh_tree()
        
        # Статусная строка
        status_frame = ttk.Frame(self.main_window)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        self.status_label = ttk.Label(status_frame, text="Готов. Горячие клавиши: Ctrl+1 - поиск шаблонов | Ctrl+2 - меню")
        self.status_label.pack(side=tk.LEFT)
    
    def refresh_tree(self, search_query=""):
        """Обновить дерево шаблонов"""
        self.tree.delete(*self.tree.get_children())
        
        if search_query:
            # Показать результаты поиска
            results = self.template_manager.search_templates(search_query)
            for template in results:
                path = template.get_path()
                icon = "📁" if template.is_folder else "📄"
                self.tree.insert("", tk.END, text=f"{icon} {template.name}", 
                               values=(path,), tags=("search_result",))
        else:
            # Показать полную структуру
            self._add_node_to_tree("", self.template_manager.root)
    
    def _add_node_to_tree(self, parent, node):
        """Добавить узел в дерево"""
        for child in node.children.values():
            icon = "📁" if child.is_folder else "📄"
            # В Treeview сохраняем путь до узла как значение (строка). Сохранение объекта в values
            # приводит к строковой сериализации и мешает корректному доступу.
            path = child.get_path()
            item_id = self.tree.insert(parent, tk.END, text=f"{icon} {child.name}", 
                                     values=(path,), tags=("folder" if child.is_folder else "template",))
            if child.is_folder:
                self._add_node_to_tree(item_id, child)
    
    def on_tree_select(self, event):
        """Обработка выбора элемента в дереве"""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            values = self.tree.item(item, 'values')
            if values:
                path = values[0]
                node = self.template_manager.get_node_by_path(path)
                if node:
                    if not node.is_folder:
                        self.preview_text.delete(1.0, tk.END)
                        self.preview_text.insert(1.0, node.content)
                    else:
                        self.preview_text.delete(1.0, tk.END)
                        self.preview_text.insert(1.0, f"Папка: {node.name}\nСодержит {len(node.children)} элементов")
    
    def on_tree_double_click(self, event):
        """Обработка двойного клика по элементу дерева"""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            values = self.tree.item(item, 'values')
            if values:
                path = values[0]
                node = self.template_manager.get_node_by_path(path)
                if node and not node.is_folder:
                    self.copy_to_clipboard()
    
    def on_tree_right_click(self, event):
        """Обработка правого клика по дереву"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
        self.context_menu.post(event.x_root, event.y_root)
    
    def on_search(self, *args):
        """Обработка поиска"""
        query = self.search_var.get()
        self.refresh_tree(query)
    
    def get_selected_node(self):
        """Получить выбранный узел"""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            values = self.tree.item(item, 'values')
            if values:
                path = values[0]
                return self.template_manager.get_node_by_path(path)
        return None
    
    def create_folder(self):
        """Создать новую папку"""
        name = simpledialog.askstring("Создать папку", "Введите название папки:")
        if name:
            selected_node = self.get_selected_node()
            parent = selected_node if selected_node and selected_node.is_folder else self.template_manager.root
            
            if name not in parent.children:
                new_folder = TemplateNode(name, "", True)
                parent.add_child(new_folder)
                self.template_manager.save_templates()
                self.refresh_tree()
                self.status_label.config(text=f"Папка '{name}' создана")
            else:
                messagebox.showerror("Ошибка", "Папка с таким названием уже существует")
    
    def create_template(self):
        """Создать новый шаблон"""
        dialog = TemplateDialog(self.main_window)
        if dialog.result:
            name, content = dialog.result
            selected_node = self.get_selected_node()
            parent = selected_node if selected_node and selected_node.is_folder else self.template_manager.root
            
            if name not in parent.children:
                new_template = TemplateNode(name, content)
                parent.add_child(new_template)
                self.template_manager.save_templates()
                self.refresh_tree()
                self.status_label.config(text=f"Шаблон '{name}' создан")
            else:
                messagebox.showerror("Ошибка", "Шаблон с таким названием уже существует")
    
    def edit_selected(self):
        """Редактировать выбранный элемент"""
        node = self.get_selected_node()
        if node:
            if node.is_folder:
                new_name = simpledialog.askstring("Редактировать папку", "Новое название:", initialvalue=node.name)
                if new_name and new_name != node.name:
                    if node.parent and new_name not in node.parent.children:
                        del node.parent.children[node.name]
                        node.name = new_name
                        node.parent.children[new_name] = node
                        self.template_manager.save_templates()
                        self.refresh_tree()
                        self.status_label.config(text=f"Папка переименована в '{new_name}'")
                    else:
                        messagebox.showerror("Ошибка", "Папка с таким названием уже существует")
            else:
                dialog = TemplateDialog(self.main_window, node.name, node.content)
                if dialog.result:
                    new_name, new_content = dialog.result
                    if new_name != node.name:
                        if node.parent and new_name not in node.parent.children:
                            del node.parent.children[node.name]
                            node.name = new_name
                            node.parent.children[new_name] = node
                        else:
                            messagebox.showerror("Ошибка", "Шаблон с таким названием уже существует")
                            return
                    
                    node.content = new_content
                    self.template_manager.save_templates()
                    self.refresh_tree()
                    # Обновить предпросмотр: выбрать элемент снова по пути (имя могло измениться)
                    self.on_tree_select(None)
                    self.status_label.config(text=f"Шаблон '{node.name}' обновлен")
    
    def delete_selected(self):
        """Удалить выбранный элемент"""
        node = self.get_selected_node()
        if node and node.parent:
            if messagebox.askyesno("Подтверждение", f"Удалить {'папку' if node.is_folder else 'шаблон'} '{node.name}'?"):
                node.parent.remove_child(node.name)
                self.template_manager.save_templates()
                self.refresh_tree()
                self.preview_text.delete(1.0, tk.END)
                self.status_label.config(text=f"{'Папка' if node.is_folder else 'Шаблон'} '{node.name}' удален")
    
    def copy_to_clipboard(self):
        """Копировать выбранный шаблон в буфер обмена"""
        node = self.get_selected_node()
        if node and not node.is_folder:
            pyperclip.copy(node.content)
            self.status_label.config(text=f"Шаблон '{node.name}' скопирован в буфер обмена")
            messagebox.showinfo("Готово", f"Текст шаблона '{node.name}' скопирован в буфер обмена")
    
    def show_hotkeys(self):
        """Показать информацию о горячих клавишах"""
        hotkey_1 = self.config_manager.get_hotkey("search_templates")
        hotkey_2 = self.config_manager.get_hotkey("cascading_menu")
        
        info = f"""Горячие клавиши TextPaster:

{hotkey_1} - Открыть окно поиска шаблонов по названию и содержимому
{hotkey_2} - Открыть каскадное меню выбора шаблона (как контекстное меню)

В основном окне:
F2 - Редактировать выбранный элемент
Delete - Удалить выбранный элемент  
Enter - Копировать шаблон в буфер обмена
Ctrl+F - Фокус на поиске

В окне поиска:
Печать - Поиск по названию и содержимому шаблонов
↑↓ - Навигация по результатам
Enter - Копировать выбранный шаблон
Esc - Закрыть окно поиска

В каскадном меню:
Наведение мыши - Показать подменю папки
Клик - Выбрать шаблон"""
        
        messagebox.showinfo("Горячие клавиши", info)
    
    def show_hotkey_settings(self):
        """Показать диалог для переназначения горячих клавиш"""
        dialog = HotKeySettingsDialog(self.main_window, self.config_manager)
        if dialog.changed:
            messagebox.showinfo("Информация", "Горячие клавиши обновлены. Пожалуйста, перезагрузите приложение для применения изменений.")

    def toggle_auto_paste(self):
        """Сохранить настройку быстрой вставки"""
        if hasattr(self, "auto_paste_var"):
            self.config_manager.set_feature("auto_paste", self.auto_paste_var.get())

    def is_auto_paste_enabled(self):
        """Проверить, включена ли быстрая вставка"""
        if hasattr(self, "auto_paste_var"):
            return bool(self.auto_paste_var.get())
        return self.config_manager.get_feature("auto_paste", False)

    def _simulate_paste(self):
        """Смоделировать Ctrl+V в активном окне"""
        controller = keyboard.Controller()
        try:
            controller.press(Key.ctrl_l)
            time.sleep(0.02)
            controller.press(KeyCode.from_char('v'))
            controller.release(KeyCode.from_char('v'))
            time.sleep(0.02)
            controller.release(Key.ctrl_l)
        except Exception as e:
            print(f"Ошибка быстрой вставки: {e}")
            try:
                controller.release(Key.ctrl_l)
            except Exception:
                pass
    
    def move_selected_up(self):
        """Переместить выбранный элемент вверх"""
        node = self.get_selected_node()
        if node and node.parent:
            if node.parent.move_child_up(node.name):
                self.template_manager.save_templates()
                self.refresh_tree()
                self.status_label.config(text=f"'{node.name}' перемещен выше")
            else:
                messagebox.showinfo("Информация", "Элемент уже находится в начале списка")
        else:
            messagebox.showwarning("Ошибка", "Выберите элемент для перемещения")
    
    def move_selected_down(self):
        """Переместить выбранный элемент вниз"""
        node = self.get_selected_node()
        if node and node.parent:
            if node.parent.move_child_down(node.name):
                self.template_manager.save_templates()
                self.refresh_tree()
                self.status_label.config(text=f"'{node.name}' перемещен ниже")
            else:
                messagebox.showinfo("Информация", "Элемент уже находится в конце списка")
        else:
            messagebox.showwarning("Ошибка", "Выберите элемент для перемещения")
    
    def move_selected_to_folder(self):
        """Переместить выбранный элемент в другую папку"""
        node = self.get_selected_node()
        if not node or not node.parent:
            messagebox.showwarning("Ошибка", "Выберите элемент для перемещения")
            return
        
        # Создать диалог выбора папки назначения
        dialog = MoveToFolderDialog(self.main_window, self.template_manager, node)
        if dialog.result:
            target_parent = dialog.result
            if target_parent == node.parent:
                messagebox.showinfo("Информация", "Элемент уже находится в этой папке")
                return
            
            # Переместить элемент
            node.parent.remove_child(node.name)
            target_parent.add_child(node)
            self.template_manager.save_templates()
            self.refresh_tree()
            self.status_label.config(text=f"'{node.name}' перемещен в '{target_parent.name}'")
    
    def init_hotkeys(self):
        """Инициализация глобальных горячих клавиш"""
        # Получить горячие клавиши из конфигурации
        hotkey_1 = self.config_manager.get_hotkey("search_templates")
        hotkey_2 = self.config_manager.get_hotkey("cascading_menu")
        
        # Tkinter требует, чтобы все операции с GUI выполнялись в главном потоке.
        # Глобальные хоткеи от pynput работают в отдельном потоке, поэтому любые вызовы
        # GUI нужно делегировать в основной цикл через .after().
        def _on_hotkey_1_mainthread():
            """Горячая клавиша 1: показать всплывающее окно быстрого выбора"""
            try:
                if self.popup_window is None:
                    self.show_popup_selector()
                else:
                    try:
                        exists = self.popup_window.window.winfo_exists()
                        if not exists:
                            self.show_popup_selector()
                    except Exception:
                        self.show_popup_selector()
            except Exception as e:
                print(f"Ошибка в обработчике горячей клавиши 1: {e}")

        def _on_hotkey_2_mainthread():
            """Горячая клавиша 2: показать каскадное меню"""
            try:
                self.cascading_menu.show()
            except Exception as e:
                print(f"Ошибка в обработчике горячей клавиши 2: {e}")

        def on_hotkey_1():
            try:
                if self.main_window:
                    self.main_window.after(0, _on_hotkey_1_mainthread)
                else:
                    _on_hotkey_1_mainthread()
            except Exception as e:
                print(f"Ошибка в on_hotkey_1: {e}")

        def on_hotkey_2():
            try:
                if self.main_window:
                    self.main_window.after(0, _on_hotkey_2_mainthread)
                else:
                    _on_hotkey_2_mainthread()
            except Exception as e:
                print(f"Ошибка в on_hotkey_2: {e}")
        
        def hotkey_thread():
            try:
                # Создаем слушатель горячих клавиш для обоих хоткеев
                hotkeys_dict = {
                    hotkey_1: on_hotkey_1,
                    hotkey_2: on_hotkey_2
                }
                self.hotkeys_handle = keyboard.GlobalHotKeys(hotkeys_dict)
                self.hotkeys_handle.start()
                
                # Бесконечный цикл для поддержания работы
                while True:
                    time.sleep(0.1)
                    
            except Exception as e:
                print(f"Ошибка горячих клавиш: {e}")
                print("Горячие клавиши отключены. Запустите программу от имени администратора.")
                print("Альтернатива: используйте кнопки в главном окне.")
        
        self.hotkey_thread = threading.Thread(target=hotkey_thread, daemon=True)
        self.hotkey_thread.start()
    
    def show_popup_selector(self):
        """Показать окно поиска шаблонов"""
        # Закрываем существующее окно, если оно есть
        if self.popup_window:
            try:
                self.popup_window.close()
            except:
                pass
            self.popup_window = None
        
        # Используем новое окно поиска вместо старого навигационного
        self.popup_window = TemplateSearchDialog(self.template_manager, self.on_template_selected)
    
    def on_template_selected(self, template, source=None):
        """Обработка выбора шаблона во всплывающем окне"""
        if template and not template.is_folder:
            pyperclip.copy(template.content)
            # Показать уведомление в трее (опционально)
            print(f"Шаблон '{template.name}' скопирован в буфер обмена")
            if source == "cascading_menu" and self.is_auto_paste_enabled():
                self.main_window.after(50, self._simulate_paste)
    
    def run(self):
        """Запуск приложения"""
        self.main_window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.main_window.mainloop()
    
    def on_closing(self):
        """Обработка закрытия приложения"""
        # Закрываем меню, если оно открыто
        if self.cascading_menu:
            try:
                self.cascading_menu._cleanup_menu_handlers()
            except:
                pass
        
        self.template_manager.save_templates()
        if self.popup_window:
            try:
                self.popup_window.close()
            except:
                pass
        self.main_window.destroy()

class TemplateDialog:
    """Диалог для создания/редактирования шаблона"""
    def __init__(self, parent, name="", content=""):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Шаблон" if not name else f"Редактирование: {name}")
        self.dialog.geometry("600x530")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Название
        name_frame = ttk.Frame(self.dialog)
        name_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(name_frame, text="Название:").pack(side=tk.LEFT)
        self.name_var = tk.StringVar(value=name)
        name_entry = ttk.Entry(name_frame, textvariable=self.name_var)
        name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        
        # Содержимое
        content_frame = ttk.LabelFrame(self.dialog, text="Содержимое шаблона")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))
        
        self.content_text = tk.Text(content_frame, wrap=tk.WORD)
        self.content_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.content_text.insert(1.0, content)
        
        # Контекстное меню для вставки/копирования/вырезания
        self._cmenu = tk.Menu(self.dialog, tearoff=0)
        self._cmenu.add_command(label="Вырезать", command=lambda: self.content_text.event_generate('<<Cut>>'))
        self._cmenu.add_command(label="Копировать", command=lambda: self.content_text.event_generate('<<Copy>>'))
        self._cmenu.add_command(label="Вставить", command=lambda: self.content_text.event_generate('<<Paste>>'))
        self.content_text.bind('<Button-3>', lambda e: self._cmenu.post(e.x_root, e.y_root))
        
        # Поддержка Ctrl+V/Ctrl+S в диалоге (работает в Windows/Unix)
        # Привяжем к текстовому полю и полю названия
        def _paste_into(widget, event=None):
            try:
                widget.event_generate('<<Paste>>')
            except Exception:
                pass
            return 'break'

        def _save_shortcut(event=None):
            # Сохраняем и закрываем — поведение прежнего save()
            self.save()
            return 'break'

        # Кнопки фиксированы в нижней части диалога
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        self.save_button = tk.Button(button_frame, text="Сохранить", command=self.save, bg='#4CAF50', fg='white', font=('Arial', 10))
        self.save_button.pack(side=tk.RIGHT, padx=5)

        ttk.Button(button_frame, text="Отмена", command=self.cancel).pack(side=tk.RIGHT, padx=5)
        
        # Фокус на название
        name_entry.focus_set()
        name_entry.select_range(0, tk.END)

        # Привязки клавиш: Ctrl+V вставка, Ctrl+S сохранить
        # Entry и Text должны поддерживать вставку горячими клавишами; на некоторых системах
        # дефолтная обработка может быть отключена, поэтому добавим явную генерацию событий.
        name_entry.bind('<Control-v>', lambda e: _paste_into(name_entry))
        name_entry.bind('<Control-V>', lambda e: _paste_into(name_entry))
        self.content_text.bind('<Control-v>', lambda e: _paste_into(self.content_text))
        self.content_text.bind('<Control-V>', lambda e: _paste_into(self.content_text))

        # Ctrl+S для сохранения
        self.dialog.bind('<Control-s>', _save_shortcut)
        self.dialog.bind('<Control-S>', _save_shortcut)

        # Enter для сохранения, Escape для отмены
        self.dialog.bind('<Return>', lambda e: self.save())
        self.dialog.bind('<Escape>', lambda e: self.cancel())

        # Ждем закрытия диалога
        self.dialog.wait_window()
    
    def save(self):
        """Сохранить шаблон"""
        name = self.name_var.get().strip()
        content = self.content_text.get(1.0, tk.END).strip()
        
        if not name:
            messagebox.showerror("Ошибка", "Введите название шаблона")
            return
        
        self.result = (name, content)
        self.dialog.destroy()
    
    def cancel(self):
        """Отменить"""
        self.dialog.destroy()

class PopupSelector:
    """Всплывающее окно для быстрого выбора шаблона"""
    def __init__(self, template_manager, callback):
        self.template_manager = template_manager
        self.callback = callback
        self.current_node = template_manager.root
        self.hover_timer = None
        
        # Создание окна
        self.window = tk.Toplevel()
        self.window.title("Быстрый выбор шаблона")
        self.window.overrideredirect(True)  # Убрать рамку окна
        self.window.attributes('-topmost', True)  # Поверх всех окон
        
        # Размещение в центре экрана
        self.window.geometry("400x300")
        self.center_window()
        
        # Стили
        self.window.configure(bg='#f0f0f0')
        
        # Заголовок
        self.title_frame = tk.Frame(self.window, bg='#4CAF50', height=30)
        self.title_frame.pack(fill=tk.X)
        self.title_frame.pack_propagate(False)
        
        self.title_label = tk.Label(self.title_frame, text="TextPaster", 
                                   fg='white', bg='#4CAF50', font=('Arial', 12, 'bold'))
        self.title_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Кнопка закрытия
        close_btn = tk.Button(self.title_frame, text='✕', command=self.close,
                             bg='#f44336', fg='white', bd=0, font=('Arial', 10, 'bold'))
        close_btn.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # Путь
        self.path_frame = tk.Frame(self.window, bg='#e0e0e0', height=25)
        self.path_frame.pack(fill=tk.X)
        self.path_frame.pack_propagate(False)
        
        self.path_label = tk.Label(self.path_frame, text="Корень", 
                                  bg='#e0e0e0', font=('Arial', 9))
        self.path_label.pack(side=tk.LEFT, padx=10, pady=2)
        
        # Список элементов
        self.listbox = tk.Listbox(self.window, font=('Arial', 11))
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Привязка событий
        self.listbox.bind('<Motion>', self.on_mouse_motion)
        self.listbox.bind('<Leave>', self.on_mouse_leave)
        self.listbox.bind('<Button-1>', self.on_click)
        self.listbox.bind('<Double-Button-1>', self.on_double_click)
        self.window.bind('<KeyPress>', self.on_key_press)
        # Не закрываем окно при потере фокуса — это приводит к закрытию при навигации по папкам
        # self.window.bind('<FocusOut>', self.on_focus_out)
        
        self.window.focus_set()
        
        self.refresh_list()
    
    def center_window(self):
        """Центрировать окно"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
    
    def refresh_list(self):
        """Обновить список элементов"""
        self.listbox.delete(0, tk.END)
        
        # Показать кнопку "Назад" если не в корне
        if self.current_node.parent is not None:
            self.listbox.insert(tk.END, "📁 .. (Назад)")
        
        # Показать содержимое текущей папки
        folders = []
        templates = []
        
        for child in self.current_node.children.values():
            if child.is_folder:
                folders.append(child)
            else:
                templates.append(child)
        
        # Сначала папки, потом шаблоны
        for folder in sorted(folders, key=lambda x: x.name.lower()):
            self.listbox.insert(tk.END, f"📁 {folder.name}")
        
        for template in sorted(templates, key=lambda x: x.name.lower()):
            self.listbox.insert(tk.END, f"📄 {template.name}")
        
        # Обновить путь
        if self.current_node.parent is None:
            self.path_label.config(text="Корень")
        else:
            path = self.current_node.get_path()
            self.path_label.config(text=path if path else "Корень")
    
    def on_mouse_motion(self, event):
        """Обработка движения мыши"""
        index = self.listbox.nearest(event.y)
        self.listbox.selection_clear(0, tk.END)
        if 0 <= index < self.listbox.size():
            self.listbox.selection_set(index)
        
        # Сброс таймера наведения
        if self.hover_timer:
            self.window.after_cancel(self.hover_timer)
        
        # Устанавливаем новый таймер для автооткрытия папок
        self.hover_timer = self.window.after(800, lambda: self.on_hover_timeout(index))
    
    def on_mouse_leave(self, event):
        """Обработка ухода мыши"""
        if self.hover_timer:
            self.window.after_cancel(self.hover_timer)
            self.hover_timer = None
    
    def on_hover_timeout(self, index):
        """Обработка таймаута наведения"""
        if 0 <= index < self.listbox.size():
            item_text = self.listbox.get(index)
            if item_text.startswith("📁 ") and not item_text.endswith("(Назад)"):
                folder_name = item_text[2:].strip()
                if folder_name in self.current_node.children:
                    folder = self.current_node.children[folder_name]
                    if folder.is_folder:
                        self.current_node = folder
                        self.refresh_list()
    
    def on_click(self, event):
        """Обработка одиночного клика — выбрать шаблон или открыть папку через двойной клик"""
        # Одиночный клик только выделяет элемент; действие при двойном клике
        index = self.listbox.nearest(event.y)
        self.listbox.selection_clear(0, tk.END)
        if 0 <= index < self.listbox.size():
            self.listbox.selection_set(index)
    
    def on_double_click(self, event):
        """Обработка двойного клика — выбрать шаблон или открыть папку"""
        index = self.listbox.curselection()
        if not index:
            return
        
        item_text = self.listbox.get(index[0])
        
        # Если это шаблон — выбрать (скопировать)
        if item_text.startswith("📄 "):
            self.select_item(index[0])
        # Если это папка — открыть
        elif item_text.startswith("📁 "):
            self.handle_selection(index[0])
    
    def on_key_press(self, event):
        """Обработка нажатий клавиш"""
        if event.keysym == 'Escape':
            self.close()
        elif event.keysym == 'Return':
            # Enter — выбрать шаблон
            index = self.listbox.curselection()
            if index:
                self.select_item(index[0])
        elif event.keysym == 'Right':
            # Стрелка вправо — открыть папку
            index = self.listbox.curselection()
            if index:
                self.handle_selection(index[0])
        elif event.keysym == 'Left':
            # Стрелка влево — назад
            if self.current_node.parent:
                self.current_node = self.current_node.parent
                self.refresh_list()
        elif event.keysym in ['Up', 'Down']:
            # Обработка стрелок вверх/вниз — навигация по списку
            current = self.listbox.curselection()
            if event.keysym == 'Up' and current:
                new_index = max(0, current[0] - 1)
            elif event.keysym == 'Down' and current:
                new_index = min(self.listbox.size() - 1, current[0] + 1)
            elif event.keysym == 'Down':
                new_index = 0
            else:
                return
            
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(new_index)
            self.listbox.see(new_index)
    
    def handle_selection(self, index):
        """Обработка выбора элемента"""
        if index >= self.listbox.size():
            return
        
        item_text = self.listbox.get(index)
        
        if item_text == "📁 .. (Назад)":
            if self.current_node.parent:
                self.current_node = self.current_node.parent
                self.refresh_list()
        elif item_text.startswith("📁 "):
            folder_name = item_text[2:].strip()
            if folder_name in self.current_node.children:
                folder = self.current_node.children[folder_name]
                if folder.is_folder:
                    self.current_node = folder
                    self.refresh_list()
    
    def select_item(self, index):
        """Выбрать и скопировать шаблон"""
        if index >= self.listbox.size():
            return
        
        item_text = self.listbox.get(index)
        
        if item_text.startswith("📄 "):
            template_name = item_text[2:].strip()
            if template_name in self.current_node.children:
                template = self.current_node.children[template_name]
                if not template.is_folder:
                    self.callback(template)
                    self.close()
    
    def close(self):
        """Закрыть окно"""
        try:
            if hasattr(self, 'hover_timer') and self.hover_timer:
                self.window.after_cancel(self.hover_timer)
            if hasattr(self, 'window'):
                self.window.destroy()
        except:
            pass


class TemplateSearchDialog:
    """Окно поиска шаблонов по названию и содержимому"""
    def __init__(self, template_manager, callback):
        self.template_manager = template_manager
        self.callback = callback
        self.search_results = []  # Найденные шаблоны
        self.selected_template = None
        
        # Переменные для предпросмотра
        self.preview_window = None
        self.preview_timer = None
        self.last_hovered_index = -1
        
        # Создание окна
        self.window = tk.Toplevel()
        self.window.title("Поиск шаблонов")
        self.window.geometry("500x400")
        self.window.attributes('-topmost', True)
        
        # Стили
        self.window.configure(bg='#f0f0f0')
        
        # Заголовок
        self.title_frame = tk.Frame(self.window, bg='#2196F3', height=40)
        self.title_frame.pack(fill=tk.X)
        self.title_frame.pack_propagate(False)
        
        self.title_label = tk.Label(self.title_frame, text="🔍 Поиск шаблонов", 
                                   fg='white', bg='#2196F3', font=('Arial', 14, 'bold'))
        self.title_label.pack(side=tk.LEFT, padx=10, pady=8)
        
        # Поле поиска
        search_frame = tk.Frame(self.window, bg='#f0f0f0')
        search_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(search_frame, text="Введите текст для поиска:", bg='#f0f0f0', font=('Arial', 10)).pack(anchor=tk.W)
        
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', self.on_search_change)
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=('Arial', 12), width=50)
        self.search_entry.pack(fill=tk.X, pady=5)
        self.search_entry.focus()
        
        # Информация о результатах
        self.info_label = tk.Label(self.window, text="Найдено: 0 результатов", 
                                  bg='#f0f0f0', font=('Arial', 9), fg='#666')
        self.info_label.pack(fill=tk.X, padx=10, pady=2)
        
        # Список результатов
        self.results_listbox = tk.Listbox(self.window, font=('Arial', 11), selectmode=tk.SINGLE)
        self.results_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Привязка событий
        self.results_listbox.bind('<Button-1>', self.on_result_click)
        self.results_listbox.bind('<Double-Button-1>', self.on_result_double_click)
        self.results_listbox.bind('<Motion>', self.on_listbox_motion)  # Наведение мышки
        self.results_listbox.bind('<Leave>', self.on_listbox_leave)    # Уход мышки
        self.window.bind('<Return>', self.on_enter_pressed)
        self.window.bind('<Escape>', lambda e: self.close())
        self.window.bind('<Up>', self.on_key_navigation)
        self.window.bind('<Down>', self.on_key_navigation)
        
        # Кнопки
        button_frame = tk.Frame(self.window, bg='#f0f0f0')
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(button_frame, text="Выбрать (Enter)", command=self.select_result, 
                 bg='#4CAF50', fg='white', font=('Arial', 10), width=20).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Закрыть (Esc)", command=self.close, 
                 bg='#f44336', fg='white', font=('Arial', 10), width=20).pack(side=tk.LEFT, padx=5)
        
        # Центрировать окно
        self.center_window()
    
    def center_window(self):
        """Центрировать окно"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
    
    def get_all_templates(self, node=None):
        """Получить все шаблоны (не папки) из дерева"""
        if node is None:
            node = self.template_manager.root
        
        templates = []
        
        for child in node.children.values():
            if child.is_folder:
                # Рекурсивно получить шаблоны из подпапок
                templates.extend(self.get_all_templates(child))
            else:
                templates.append(child)
        
        return templates
    
    def search_templates(self, query):
        """Поиск шаблонов по названию и содержимому"""
        if not query.strip():
            return []
        
        query_lower = query.lower()
        all_templates = self.get_all_templates()
        results = []
        
        for template in all_templates:
            # Поиск по названию (точный и частичный)
            if query_lower in template.name.lower():
                results.append(template)
                continue
            
            # Поиск по содержимому
            if template.content and query_lower in template.content.lower():
                results.append(template)
        
        return results
    
    def on_search_change(self, *args):
        """Обработчик изменения текста поиска"""
        query = self.search_var.get()
        self.search_results = self.search_templates(query)
        self.update_results_display()
    
    def update_results_display(self):
        """Обновить список результатов"""
        self.results_listbox.delete(0, tk.END)
        
        # Показать результаты
        for template in self.search_results:
            # Показать путь к шаблону для контекста
            path = template.get_path()
            display_text = f"📄 {template.name}"
            if path:
                display_text += f"  ({path})"
            self.results_listbox.insert(tk.END, display_text)
        
        # Обновить информацию
        count = len(self.search_results)
        if count == 0:
            self.info_label.config(text="Найдено: 0 результатов", fg='#d32f2f')
        elif count == 1:
            self.info_label.config(text=f"Найдено: {count} результат", fg='#388e3c')
        else:
            self.info_label.config(text=f"Найдено: {count} результатов", fg='#388e3c')
        
        # Автоматически выделить первый результат
        if self.search_results:
            self.results_listbox.selection_set(0)
    
    def on_result_click(self, event):
        """Обработка клика по результату"""
        index = self.results_listbox.nearest(event.y)
        if 0 <= index < len(self.search_results):
            self.results_listbox.selection_clear(0, tk.END)
            self.results_listbox.selection_set(index)
    
    def on_result_double_click(self, event):
        """Обработка двойного клика — выбрать шаблон"""
        self.select_result()
    
    def on_key_navigation(self, event):
        """Навигация стрелками вверх/вниз"""
        current = self.results_listbox.curselection()
        
        if event.keysym == 'Up':
            if current:
                new_index = max(0, current[0] - 1)
                self.results_listbox.selection_clear(0, tk.END)
                self.results_listbox.selection_set(new_index)
                self.results_listbox.see(new_index)
        elif event.keysym == 'Down':
            if current:
                new_index = min(len(self.search_results) - 1, current[0] + 1)
            else:
                new_index = 0
            self.results_listbox.selection_clear(0, tk.END)
            self.results_listbox.selection_set(new_index)
            self.results_listbox.see(new_index)
    
    def on_enter_pressed(self, event):
        """Обработка нажатия Enter"""
        self.select_result()
    
    def on_listbox_motion(self, event):
        """Обработка наведения мышки на элемент списка"""
        index = self.results_listbox.nearest(event.y)
        
        # Если наведение на новый элемент
        if index != self.last_hovered_index and 0 <= index < len(self.search_results):
            self.last_hovered_index = index
            
            # Отменить предыдущий таймер если существует
            if self.preview_timer:
                self.window.after_cancel(self.preview_timer)
                self.preview_timer = None
            
            # Закрыть старый предпросмотр если существует
            if self.preview_window:
                self.close_preview()
            
            # Установить таймер на 1 секунды для показа предпросмотра
            self.preview_timer = self.window.after(1000, self.show_preview, index)
    
    def on_listbox_leave(self, event):
        """Обработка ухода мышки из списка"""
        self.last_hovered_index = -1
        
        # Отменить таймер
        if self.preview_timer:
            self.window.after_cancel(self.preview_timer)
            self.preview_timer = None
        
        # Закрыть предпросмотр
        if self.preview_window:
            self.close_preview()
    
    def show_preview(self, index):
        """Показать предпросмотр содержимого шаблона"""
        if not (0 <= index < len(self.search_results)):
            return
        
        template = self.search_results[index]
        
        # Создать окно предпросмотра
        self.preview_window = tk.Toplevel(self.window)
        self.preview_window.wm_overrideredirect(True)  # Убрать заголовок окна
        self.preview_window.configure(bg='#fafafa')
        
        # Получить координаты элемента списка
        listbox_x = self.results_listbox.winfo_rootx()
        listbox_y = self.results_listbox.winfo_rooty()
        item_height = self.results_listbox.winfo_height() // max(1, self.results_listbox.size())
        item_y = listbox_y + item_height * index
        
        # Показать окно над элементом
        preview_x = listbox_x - 320
        preview_y = item_y - 10
        
        # Убедиться что окно не выходит за границы экрана
        screen_width = self.preview_window.winfo_screenwidth()
        if preview_x < 0:
            preview_x = listbox_x + self.results_listbox.winfo_width() + 10
        
        # Рамка с тенью
        border_frame = tk.Frame(self.preview_window, bg='#bdbdbd')
        border_frame.pack(fill=tk.BOTH, expand=True)
        
        main_frame = tk.Frame(border_frame, bg='#fafafa')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        # Заголовок предпросмотра
        header = tk.Frame(main_frame, bg='#e3f2fd')
        header.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        header_label = tk.Label(header, text=f"📄 {template.name}", 
                               bg='#e3f2fd', font=('Arial', 11, 'bold'), fg='#1976d2')
        header_label.pack(anchor=tk.W)
        
        path_label = tk.Label(header, text=f"Путь: {template.get_path()}", 
                             bg='#e3f2fd', font=('Arial', 9), fg='#555')
        path_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Содержимое
        content_label = tk.Label(main_frame, text="Содержимое:", 
                                bg='#fafafa', font=('Arial', 10, 'bold'), fg='#333')
        content_label.pack(anchor=tk.W, padx=10)
        
        # Text виджет для отображения содержимого
        text_frame = tk.Frame(main_frame, bg='#fafafa')
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))
        
        text_widget = tk.Text(text_frame, height=10, width=40, font=('Courier', 9),
                             bg='#fff', fg='#222', wrap=tk.WORD, relief=tk.SUNKEN, bd=1)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.config(state=tk.NORMAL)
        text_widget.delete('1.0', tk.END)
        
        # Показать содержимое с обрезкой если слишком длинное
        content = template.content if template.content else "[Пусто]"
        # Обрезать содержимое если очень длинное
        if len(content) > 500:
            content = content[:500] + "\n\n[...сокращено...]"
        
        text_widget.insert('1.0', content)
        text_widget.config(state=tk.DISABLED)  # Сделать read-only
        
        # Добавить скроллбар если нужно
        scrollbar = tk.Scrollbar(text_frame, command=text_widget.yview)
        if content.count('\n') > 10:
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            text_widget.config(yscrollcommand=scrollbar.set)
        
        # Размер окна
        self.preview_window.geometry(f'380x250+{preview_x}+{preview_y}')
        self.preview_window.attributes('-topmost', True)
        self.preview_window.lift()
    
    def close_preview(self):
        """Закрыть окно предпросмотра"""
        try:
            if self.preview_window:
                self.preview_window.destroy()
                self.preview_window = None
        except:
            pass
    
    def select_result(self):
        """Выбрать найденный шаблон"""
        current = self.results_listbox.curselection()
        if not current:
            return
        
        index = current[0]
        if 0 <= index < len(self.search_results):
            self.selected_template = self.search_results[index]
            self.callback(self.selected_template)
            self.close()
    
    def close(self):
        """Закрыть окно"""
        # Отменить таймер предпросмотра
        if self.preview_timer:
            self.window.after_cancel(self.preview_timer)
            self.preview_timer = None
        
        # Закрыть окно предпросмотра
        self.close_preview()
        
        try:
            if hasattr(self, 'window'):
                self.window.destroy()
        except:
            pass


class HotKeySettingsDialog:
    """Диалог для переназначения горячих клавиш"""
    def __init__(self, parent, config_manager):
        self.config_manager = config_manager
        self.changed = False
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Переназначение горячих клавиш")
        self.dialog.geometry("550x440")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Информация
        info_label = ttk.Label(self.dialog, text="Введите новые комбинации клавиш.\nПримеры: <ctrl>+a, <shift>+f1, <alt>+p", 
                              font=('Arial', 10))
        info_label.pack(pady=10, padx=10)
        
        # Горячая клавиша 1
        frame1 = ttk.Frame(self.dialog)
        frame1.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(frame1, text="Поиск шаблонов:", font=('Arial', 10)).pack(anchor=tk.W)
        self.hotkey1_var = tk.StringVar(value=self.config_manager.get_hotkey("search_templates"))
        self.entry1 = ttk.Entry(frame1, textvariable=self.hotkey1_var, font=('Arial', 11), width=30)
        self.entry1.pack(fill=tk.X, pady=5)
        
        # Горячая клавиша 2
        frame2 = ttk.Frame(self.dialog)
        frame2.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(frame2, text="Каскадное меню:", font=('Arial', 10)).pack(anchor=tk.W)
        self.hotkey2_var = tk.StringVar(value=self.config_manager.get_hotkey("cascading_menu"))
        self.entry2 = ttk.Entry(frame2, textvariable=self.hotkey2_var, font=('Arial', 11), width=30)
        self.entry2.pack(fill=tk.X, pady=5)
        
        # Примеры
        examples = ttk.LabelFrame(self.dialog, text="Доступные комбинации", padding=10)
        examples.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        examples_text = tk.Text(examples, height=8, width=50, font=('Courier', 9), wrap=tk.WORD)
        examples_text.pack(fill=tk.BOTH, expand=True)
        
        examples_content = """<ctrl>+a, <ctrl>+1, <ctrl>+2, <ctrl>+3...
<shift>+a, <shift>+1, <shift>+f1...
<alt>+a, <alt>+1, <alt>+f1...
<alt>+shift>+a, <alt>+shift>+1...
<ctrl>+shift>+a, <ctrl>+shift>+1...

Примеры:
<ctrl>+3 - Ctrl + 3
<alt>+shift>+s - Alt + Shift + S
<ctrl>+shift>+q - Ctrl + Shift + Q"""
        
        examples_text.insert(1.0, examples_content)
        examples_text.config(state=tk.DISABLED)
        
        # Кнопки
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=15)
        
        ttk.Button(button_frame, text="Сохранить", command=self.save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Отмена", command=self.cancel).pack(side=tk.RIGHT, padx=5)
        
        self.dialog.wait_window()
    
    def save(self):
        """Сохранить новые горячие клавиши"""
        hotkey1 = self.hotkey1_var.get().strip()
        hotkey2 = self.hotkey2_var.get().strip()
        
        if not hotkey1:
            messagebox.showerror("Ошибка", "Горячая клавиша для поиска не может быть пустой")
            return
        
        if not hotkey2:
            messagebox.showerror("Ошибка", "Горячая клавиша для меню не может быть пустой")
            return
        
        if hotkey1 == hotkey2:
            messagebox.showerror("Ошибка", "Горячие клавиши должны быть разными")
            return
        
        # Сохранить в конфиг
        self.config_manager.set_hotkey("search_templates", hotkey1)
        self.config_manager.set_hotkey("cascading_menu", hotkey2)
        
        self.changed = True
        self.dialog.destroy()
    
    def cancel(self):
        """Отмена"""
        self.dialog.destroy()


class MoveToFolderDialog:
    """Диалог для выбора папки-назначения при перемещении элемента"""
    def __init__(self, parent, template_manager, node_to_move):
        self.result = None
        self.template_manager = template_manager
        self.node_to_move = node_to_move
        self.selected_folder = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Выберите папку для перемещения")
        self.dialog.geometry("400x350")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Информация
        info_label = ttk.Label(self.dialog, text=f"Куда переместить '{node_to_move.name}'?", 
                              font=('Arial', 10))
        info_label.pack(pady=10, padx=10)
        
        # Дерево папок
        self.tree = ttk.Treeview(self.dialog, selectmode='browse')
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(self.tree, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Добавить папки в дерево
        self._add_folders_to_tree("", self.template_manager.root)
        
        # Кнопки
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Отмена", command=self.cancel).pack(side=tk.RIGHT, padx=5)
        
        self.dialog.wait_window()
    
    def _add_folders_to_tree(self, parent_item, node):
        """Рекурсивно добавить папки в дерево"""
        for child in node.children.values():
            if child.is_folder and child != self.node_to_move:
                # Сохраняем ссылку на объект узла как значение в дереве
                item_id = self.tree.insert(parent_item, tk.END, text=f"📁 {child.name}", 
                                          values=(id(child),))
                # Рекурсивно добавить подпапки
                self._add_folders_to_tree(item_id, child)
    
    def ok_clicked(self):
        """Нажатие кнопки OK"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Ошибка", "Выберите папку-назначение")
            return
        
        item = selection[0]
        # Получить узел из памяти по значению
        node_id = self.tree.item(item, 'values')[0]
        
        # Найти узел по id
        self.result = self._find_node_by_id(int(node_id), self.template_manager.root)
        
        if self.result:
            self.dialog.destroy()
    
    def _find_node_by_id(self, node_id, node):
        """Рекурсивно найти узел по id"""
        if id(node) == node_id:
            return node
        
        for child in node.children.values():
            result = self._find_node_by_id(node_id, child)
            if result:
                return result
        
        return None
    
    def cancel(self):
        """Отмена"""
        self.dialog.destroy()


def main():
    """Главная функция"""
    try:
        app = TextPasterApp()
        app.run()
    except Exception as e:
        print(f"Ошибка запуска приложения: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
