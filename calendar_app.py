from kivy.app import App
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle, Line
from datetime import datetime, timedelta
import json
import os
import calendar
import re

Window.size = (600, 750)
Window.clearcolor = (0.93, 0.95, 0.98, 1)  # Світло-голубий фон
Window.title = "Календар Нагадувань"

class DayButton(Button):
    """Кнопка для дня календаря з індикатором подій"""
    def __init__(self, day, is_today=False, is_other_month=False, has_reminders=False, **kwargs):
        super(DayButton, self).__init__(**kwargs)
        self.day = day
        self.is_today = is_today
        self.is_other_month = is_other_month
        self.has_reminders = has_reminders
        self.size_hint = (None, None)
        self.size = (70, 70)
        
        if day > 0:
            self.text = str(day)
        else:
            self.text = ''
            self.disabled = True
        
        self.update_style()
    
    def update_style(self):
        """Оновлює стиль кнопки"""
        if self.is_other_month or self.day <= 0:
            self.background_color = (0.95, 0.95, 0.95, 0.3)
            self.color = (0.7, 0.7, 0.7, 0.5)
        elif self.is_today:
            self.background_color = (0.4, 0.6, 0.85, 1) 
            self.color = (1, 1, 1, 1)
            self.bold = True
        elif self.has_reminders:
            self.background_color = (0.5, 0.7, 0.9, 1) 
            self.color = (1, 1, 1, 1)
        else:
            self.background_color = (1, 1, 1, 1)
            self.color = (0.2, 0.3, 0.4, 1)
        
        self.font_size = 18

class BulkAddPopup(Popup):
    """Вікно для масового додавання подій"""
    def __init__(self, app_instance, **kwargs):
        super(BulkAddPopup, self).__init__(**kwargs)
        self.app_instance = app_instance
        
        self.title = "Масове додавання подій"
        self.size_hint = (0.95, 0.9)
        
        main_layout = BoxLayout(orientation='vertical', spacing=15, padding=15)
        
        instruction = Label(
            text='Введіть події у форматі: дд чч подія\nНаприклад: 25 14 Зустріч з клієнтом\n(дд - день місяця, чч - година)',
            font_size=14,
            size_hint_y=None,
            height=70,
            color=(0.3, 0.5, 0.7, 1),
            halign='center'
        )
        
        self.events_input = TextInput(
            hint_text='25 14 Зустріч з клієнтом\n26 10 Дзвінок партнеру\n27 15 Презентація проекту',
            multiline=True,
            font_size=14,
            background_color=(1, 1, 1, 1)
        )
        
        month_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=10)
        month_layout.add_widget(Label(text='Місяць:', size_hint_x=0.3, color=(0.3, 0.4, 0.5, 1)))
        
        months_ua = ['Січень', 'Лютий', 'Березень', 'Квітень', 'Травень', 'Червень',
                     'Липень', 'Серпень', 'Вересень', 'Жовтень', 'Листопад', 'Грудень']
        
        current_month_idx = datetime.now().month - 1
        self.month_spinner = Spinner(
            text=months_ua[current_month_idx],
            values=months_ua,
            size_hint_x=0.7
        )
        month_layout.add_widget(self.month_spinner)
        
        year_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=10)
        year_layout.add_widget(Label(text='Рік:', size_hint_x=0.3, color=(0.3, 0.4, 0.5, 1)))
        
        current_year = datetime.now().year
        years = [str(y) for y in range(current_year, current_year + 3)]
        self.year_spinner = Spinner(
            text=str(current_year),
            values=years,
            size_hint_x=0.7
        )
        year_layout.add_widget(self.year_spinner)
        
        self.result_label = Label(
            text='Введіть події вище',
            font_size=12,
            size_hint_y=None,
            height=30,
            color=(0.4, 0.5, 0.6, 1)
        )

        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        
        preview_btn = Button(
            text='Перевірити',
            background_color=(0.5, 0.65, 0.8, 1),
            font_size=14
        )
        preview_btn.bind(on_press=self.preview_events)
        
        add_btn = Button(
            text='Додати всі',
            background_color=(0.4, 0.6, 0.85, 1),
            font_size=14
        )
        add_btn.bind(on_press=self.add_all_events)
        
        close_btn = Button(
            text='Закрити',
            background_color=(0.6, 0.7, 0.8, 1),
            font_size=14
        )
        close_btn.bind(on_press=self.dismiss)
        
        btn_layout.add_widget(preview_btn)
        btn_layout.add_widget(add_btn)
        btn_layout.add_widget(close_btn)
        

        main_layout.add_widget(instruction)
        main_layout.add_widget(month_layout)
        main_layout.add_widget(year_layout)
        main_layout.add_widget(self.events_input)
        main_layout.add_widget(self.result_label)
        main_layout.add_widget(btn_layout)
        
        self.content = main_layout
    
    def parse_events(self):
        """Парсить введені події"""
        text = self.events_input.text.strip()
        if not text:
            return []
        
        lines = text.split('\n')
        events = []
        

        months_ua = ['Січень', 'Лютий', 'Березень', 'Квітень', 'Травень', 'Червень',
                     'Липень', 'Серпень', 'Вересень', 'Жовтень', 'Листопад', 'Грудень']
        month = months_ua.index(self.month_spinner.text) + 1
        year = int(self.year_spinner.text)
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            

            match = re.match(r'^(\d{1,2})\s+(\d{1,2}):?(\d{0,2})\s+(.+)$', line)
            
            if match:
                day = int(match.group(1))
                hour = int(match.group(2))
                minute = int(match.group(3)) if match.group(3) else 0
                event_text = match.group(4).strip()
                
      
                try:
            
                    date_obj = datetime(year, month, day, hour, minute)
                    
             
                    if date_obj > datetime.now():
                        events.append({
                            'day': day,
                            'hour': hour,
                            'minute': minute,
                            'text': event_text,
                            'datetime': date_obj
                        })
                    else:
                        events.append({
                            'day': day,
                            'hour': hour,
                            'minute': minute,
                            'text': event_text,
                            'error': 'Минула дата'
                        })
                except ValueError as e:
                    events.append({
                        'line': line,
                        'error': f'Некоректна дата: {str(e)}'
                    })
            else:
                events.append({
                    'line': line,
                    'error': 'Неправильний формат'
                })
        
        return events
    
    def preview_events(self, instance):
        """Показує попередній перегляд подій"""
        events = self.parse_events()
        
        if not events:
            self.result_label.text = 'Немає подій для додавання'
            return
        
        valid_count = sum(1 for e in events if 'error' not in e)
        error_count = len(events) - valid_count
        
        self.result_label.text = f'Знайдено: {valid_count} коректних, {error_count} помилок'
 
        if error_count > 0:
            errors = [e for e in events if 'error' in e]
            error_text = '\n'.join([f"• {e.get('line', '')} - {e['error']}" for e in errors[:3]])
            self.show_message('Попередження', 
                            f'Коректних подій: {valid_count}\nПомилок: {error_count}\n\nПриклади помилок:\n{error_text}')
    
    def add_all_events(self, instance):
        """Додає всі події"""
        events = self.parse_events()
        
        if not events:
            self.show_message('Помилка', 'Немає подій для додавання!')
            return
        
        valid_events = [e for e in events if 'error' not in e]
        
        if not valid_events:
            self.show_message('Помилка', 'Всі події мають помилки!\nПеревірте формат: дд чч подія')
            return
        

        added_count = 0
        for event in valid_events:
            reminder = {
                'id': len(self.app_instance.reminders) + 1 + added_count,
                'title': event['text'],
                'date': event['datetime'].strftime('%d.%m.%Y'),
                'time': f"{event['hour']:02d}:{event['minute']:02d}",
                'datetime': event['datetime'].isoformat(),
                'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.app_instance.reminders.append(reminder)
            added_count += 1

        self.app_instance.reminders.sort(key=lambda x: x.get('datetime', ''))

        self.app_instance.save_reminders()
        self.app_instance.update_calendar()
        
        self.show_message('Успіх', f'Додано {added_count} подій!')
        self.dismiss()
    
    def show_message(self, title, message):
        """Показує повідомлення"""
        popup_layout = BoxLayout(orientation='vertical', spacing=15, padding=20)
        
        popup_layout.add_widget(Label(
            text=message,
            font_size=14,
            text_size=(400, None),
            halign='center',
            color=(0.2, 0.3, 0.4, 1)
        ))
        
        ok_btn = Button(
            text='OK',
            size_hint_y=None,
            height=45,
            background_color=(0.4, 0.6, 0.85, 1)
        )
        
        popup = Popup(
            title=title,
            content=popup_layout,
            size_hint=(0.8, 0.6)
        )
        
        ok_btn.bind(on_press=popup.dismiss)
        popup_layout.add_widget(ok_btn)
        popup.open()

class ReminderDetailPopup(Popup):
    """Спливаюче вікно для перегляду та додавання нагадувань на обраний день"""
    def __init__(self, date_obj, app_instance, **kwargs):
        super(ReminderDetailPopup, self).__init__(**kwargs)
        self.date_obj = date_obj
        self.app_instance = app_instance
  
        months_ua = ['Січня', 'Лютого', 'Березня', 'Квітня', 'Травня', 'Червня',
                     'Липня', 'Серпня', 'Вересня', 'Жовтня', 'Листопада', 'Грудня']
        
        date_str = f"{date_obj.day} {months_ua[date_obj.month - 1]} {date_obj.year}"
        
        self.title = f"{date_str}"
        self.size_hint = (0.95, 0.9)
        
        main_layout = BoxLayout(orientation='vertical', spacing=15, padding=15)
        
        add_section = BoxLayout(orientation='vertical', size_hint_y=None, height=180, spacing=10)
        
        add_title = Label(
            text='Додати нове нагадування',
            font_size=18,
            size_hint_y=None,
            height=30,
            color=(0.3, 0.5, 0.7, 1),
            bold=True
        )
        
   
        text_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=10)
        text_layout.add_widget(Label(text='Текст:', size_hint_x=0.2, color=(0.3, 0.3, 0.3, 1)))
        
        self.reminder_input = TextInput(
            hint_text='Введіть текст нагадування...',
            multiline=False,
            size_hint_x=0.8,
            font_size=14
        )
        text_layout.add_widget(self.reminder_input)
        
        time_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=10)
        time_layout.add_widget(Label(text='Час:', size_hint_x=0.2, color=(0.3, 0.3, 0.3, 1)))
        
        self.hour_spinner = Spinner(
            text='12',
            values=[f'{i:02d}' for i in range(24)],
            size_hint_x=0.3
        )
        
        time_layout.add_widget(self.hour_spinner)
        time_layout.add_widget(Label(text=':', size_hint_x=0.1))
        
        self.minute_spinner = Spinner(
            text='00',
            values=[f'{i:02d}' for i in range(0, 60, 5)],
            size_hint_x=0.3
        )
        
        time_layout.add_widget(self.minute_spinner)

        add_btn = Button(
            text='Додати',
            size_hint_y=None,
            height=45,
            background_color=(0.4, 0.6, 0.85, 1),
            font_size=16
        )
        add_btn.bind(on_press=self.add_reminder)
        
        add_section.add_widget(add_title)
        add_section.add_widget(text_layout)
        add_section.add_widget(time_layout)
        add_section.add_widget(add_btn)
        

        divider = Label(
            text='─' * 50,
            size_hint_y=None,
            height=20,
            color=(0.7, 0.7, 0.7, 1)
        )
        
  
        list_title = Label(
            text='Нагадування на цей день',
            font_size=18,
            size_hint_y=None,
            height=30,
            color=(0.3, 0.4, 0.5, 1),
            bold=True
        )
        

        self.reminders_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        self.reminders_layout.bind(minimum_height=self.reminders_layout.setter('height'))
        
        scroll = ScrollView()
        scroll.add_widget(self.reminders_layout)

        close_btn = Button(
            text='Закрити',
            size_hint_y=None,
            height=50,
            background_color=(0.6, 0.7, 0.8, 1),
            font_size=16
        )
        close_btn.bind(on_press=self.dismiss)

        main_layout.add_widget(add_section)
        main_layout.add_widget(divider)
        main_layout.add_widget(list_title)
        main_layout.add_widget(scroll)
        main_layout.add_widget(close_btn)
        
        self.content = main_layout
        
   
        self.load_day_reminders()
    
    def add_reminder(self, instance):
        """Додає нове нагадування"""
        text = self.reminder_input.text.strip()
        
        if not text:
            self.show_message('Помилка', 'Введіть текст нагадування!')
            return
        
        hour = int(self.hour_spinner.text)
        minute = int(self.minute_spinner.text)
        
 
        reminder_datetime = datetime.combine(self.date_obj, datetime.min.time())
        reminder_datetime = reminder_datetime.replace(hour=hour, minute=minute)
        
 
        if reminder_datetime <= datetime.now():
            self.show_message('Помилка', 'Час нагадування має бути в майбутньому!')
            return
        
  
        reminder = {
            'id': len(self.app_instance.reminders) + 1,
            'title': text,
            'date': self.date_obj.strftime('%d.%m.%Y'),
            'time': f'{hour:02d}:{minute:02d}',
            'datetime': reminder_datetime.isoformat(),
            'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.app_instance.reminders.append(reminder)
        self.app_instance.save_reminders()
      
        self.load_day_reminders()
        self.app_instance.update_calendar()
    
        self.reminder_input.text = ''
        
        self.show_message('Успіх', 'Нагадування додано!')
    
    def load_day_reminders(self):
        """Завантажує нагадування для обраного дня"""
        self.reminders_layout.clear_widgets()
        
        date_str = self.date_obj.strftime('%d.%m.%Y')
        day_reminders = [r for r in self.app_instance.reminders if r.get('date') == date_str]
        
        if not day_reminders:
            empty_label = Label(
                text='Немає нагадувань на цей день',
                font_size=14,
                color=(0.5, 0.6, 0.7, 1),
                size_hint_y=None,
                height=40
            )
            self.reminders_layout.add_widget(empty_label)
        else:
            day_reminders.sort(key=lambda x: x.get('time', '00:00'))
            
            for reminder in day_reminders:
                reminder_item = self.create_reminder_item(reminder)
                self.reminders_layout.add_widget(reminder_item)
    
    def create_reminder_item(self, reminder):
        """Створює елемент списку нагадування"""
        item_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=70,
            padding=10,
            spacing=10
        )
        
    
        info_layout = BoxLayout(orientation='vertical', size_hint_x=0.75)
        
        title_label = Label(
            text=reminder['title'],
            font_size=16,
            text_size=(400, None),
            halign='left',
            valign='top',
            color=(0.2, 0.3, 0.4, 1)
        )
        
        time_label = Label(
            text=f"{reminder.get('time', '00:00')}",
            font_size=14,
            text_size=(400, None),
            halign='left',
            valign='bottom',
            color=(0.4, 0.5, 0.6, 1)
        )
        
        info_layout.add_widget(title_label)
        info_layout.add_widget(time_label)
        
   
        delete_btn = Button(
            text='Видалити',
            size_hint_x=0.25,
            font_size=14,
            background_color=(0.7, 0.75, 0.8, 1)
        )
        delete_btn.bind(on_press=lambda x: self.delete_reminder(reminder))
        
        item_layout.add_widget(info_layout)
        item_layout.add_widget(delete_btn)
        
        return item_layout
    
    def delete_reminder(self, reminder):
        """Видаляє нагадування"""
        self.app_instance.reminders = [r for r in self.app_instance.reminders if r['id'] != reminder['id']]
        self.app_instance.save_reminders()
        self.load_day_reminders()
        self.app_instance.update_calendar()
        self.show_message('Видалено', 'Нагадування видалено!')
    
    def show_message(self, title, message):
        """Показує коротке повідомлення"""
        popup_layout = BoxLayout(orientation='vertical', spacing=15, padding=20)
        
        popup_layout.add_widget(Label(
            text=message,
            font_size=16,
            text_size=(300, None),
            halign='center'
        ))
        
        ok_btn = Button(
            text='OK',
            size_hint_y=None,
            height=45,
            background_color=(0.4, 0.6, 0.85, 1)
        )
        
        popup = Popup(
            title=title,
            content=popup_layout,
            size_hint=(0.7, 0.4)
        )
        
        ok_btn.bind(on_press=popup.dismiss)
        popup_layout.add_widget(ok_btn)
        popup.open()

class CalendarApp(App):
    def __init__(self):
        super().__init__()
        self.reminders = []
        self.current_date = datetime.now().date()
        self.load_reminders()
        
    def build(self):
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        

        header = BoxLayout(orientation='vertical', size_hint_y=None, height=100, spacing=5)
        
        app_title = Label(
            text='Календар Нагадувань',
            font_size=28,
            size_hint_y=None,
            height=50,
            color=(0.3, 0.5, 0.7, 1),
            bold=True
        )
  
        self.stats_label = Label(
            text='Всього нагадувань: 0',
            font_size=14,
            size_hint_y=None,
            height=30,
            color=(0.4, 0.5, 0.6, 1)
        )
        
        header.add_widget(app_title)
        header.add_widget(self.stats_label)
    
        nav_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=60, spacing=10, padding=[10, 5])
        
        prev_btn = Button(
            text='Попередній',
            size_hint_x=0.3,
            background_color=(0.5, 0.65, 0.8, 1),
            font_size=14
        )
        prev_btn.bind(on_press=self.prev_month)
        
        self.month_year_label = Label(
            text='',
            font_size=22,
            color=(0.3, 0.4, 0.5, 1),
            bold=True
        )
        
        next_btn = Button(
            text='Наступний',
            size_hint_x=0.3,
            background_color=(0.5, 0.65, 0.8, 1),
            font_size=14
        )
        next_btn.bind(on_press=self.next_month)
        
        today_btn = Button(
            text='Сьогодні',
            size_hint_x=0.25,
            background_color=(0.4, 0.6, 0.85, 1),
            font_size=14
        )
        today_btn.bind(on_press=self.goto_today)
        
        nav_layout.add_widget(prev_btn)
        nav_layout.add_widget(self.month_year_label)
        nav_layout.add_widget(today_btn)
        nav_layout.add_widget(next_btn)

        bulk_add_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10, padding=[10, 5])
        
        bulk_add_btn = Button(
            text='Додати багато подій',
            background_color=(0.3, 0.5, 0.7, 1),
            font_size=16,
            bold=True
        )
        bulk_add_btn.bind(on_press=self.open_bulk_add)
        
        bulk_add_layout.add_widget(bulk_add_btn)
        
 
        self.calendar_grid = GridLayout(cols=7, spacing=5, padding=10)
        
    
        days_ua = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд']
        for day in days_ua:
            day_label = Label(
                text=day,
                font_size=16,
                color=(0.3, 0.5, 0.7, 1),
                bold=True,
                size_hint_y=None,
                height=30
            )
            self.calendar_grid.add_widget(day_label)
        
        legend_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=20, padding=[20, 5])
        
        legend_items = [
            ('Сьогодні', (0.4, 0.6, 0.85, 1)),
            ('Є нагадування', (0.5, 0.7, 0.9, 1)),
            ('Звичайний день', (1, 1, 1, 1))
        ]
        
        for text, color in legend_items:   
            item_layout = BoxLayout(orientation='horizontal', spacing=5)
            
            color_box = Label(
                text='@',
                font_size=20,
                color=color,
                size_hint_x=0.2
            )
            
            text_label = Label(
                text=text,
                font_size=12,
                color=(0.4, 0.5, 0.6, 1),
                size_hint_x=0.8
            )
            
            item_layout.add_widget(color_box)
            item_layout.add_widget(text_label)
            legend_layout.add_widget(item_layout)
        
        main_layout.add_widget(header)
        main_layout.add_widget(nav_layout)
        main_layout.add_widget(bulk_add_layout)
        main_layout.add_widget(self.calendar_grid)
        main_layout.add_widget(legend_layout)
        
        self.update_calendar()
        self.schedule_notifications()
        
        return main_layout
    
    def update_calendar(self):
        """Оновлює відображення календаря"""

        calendar_children = list(self.calendar_grid.children)
        for child in calendar_children[:-7]: 
            self.calendar_grid.remove_widget(child)
        
       
        months_ua = ['Січень', 'Лютий', 'Березень', 'Квітень', 'Травень', 'Червень',
                     'Липень', 'Серпень', 'Вересень', 'Жовтень', 'Листопад', 'Грудень']
        
        self.month_year_label.text = f"{months_ua[self.current_date.month - 1]} {self.current_date.year}"
        

        total_count = len(self.reminders)
        today_count = len([r for r in self.reminders 
                          if r.get('date') == datetime.now().strftime('%d.%m.%Y')])
        self.stats_label.text = f'Всього нагадувань: {total_count} | Сьогодні: {today_count}'
 
        cal = calendar.monthcalendar(self.current_date.year, self.current_date.month)
        today = datetime.now().date()
     
        for week in cal:
            for day in week:
                if day == 0:
               
                    empty_label = Label(text='', size_hint=(None, None), size=(70, 70))
                    self.calendar_grid.add_widget(empty_label)
                else:
                    date_obj = datetime(self.current_date.year, self.current_date.month, day).date()
                    
           
                    date_str = date_obj.strftime('%d.%m.%Y')
                    has_reminders = any(r.get('date') == date_str for r in self.reminders)
                    
                   
                    day_btn = DayButton(
                        day=day,
                        is_today=(date_obj == today),
                        has_reminders=has_reminders
                    )
                    
                    day_btn.bind(on_press=lambda x, d=date_obj: self.open_day_detail(d))
                    
                    self.calendar_grid.add_widget(day_btn)
    
    def open_day_detail(self, date_obj):
        """Відкриває деталі дня"""
        popup = ReminderDetailPopup(date_obj, self)
        popup.open()
    
    def open_bulk_add(self, instance):
        """Відкриває вікно масового додавання подій"""
        popup = BulkAddPopup(self)
        popup.open()
    
    def prev_month(self, instance):
        """Перехід до попереднього місяця"""
        if self.current_date.month == 1:
            self.current_date = self.current_date.replace(year=self.current_date.year - 1, month=12)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month - 1)
        self.update_calendar()
    
    def next_month(self, instance):
        """Перехід до наступного місяця"""
        if self.current_date.month == 12:
            self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month + 1)
        self.update_calendar()
    
    def goto_today(self, instance):
        """Перехід до поточного місяця"""
        self.current_date = datetime.now().date()
        self.update_calendar()
    
    def schedule_notifications(self):
        """Планує перевірку нагадувань"""
        Clock.schedule_interval(self.check_reminders, 60)
    
    def check_reminders(self, dt):
        """Перевіряє нагадування"""
        now = datetime.now()
        
        for reminder in self.reminders[:]:
            if 'datetime' in reminder:
                reminder_datetime = datetime.fromisoformat(reminder['datetime'])
                
                if (abs((reminder_datetime - now).total_seconds()) < 60 and 
                    reminder_datetime <= now):
                    
                    self.show_notification(reminder)
                    self.reminders.remove(reminder)
                    self.save_reminders()
                    self.update_calendar()
    
    def show_notification(self, reminder):
        """Показує сповіщення"""
        popup_layout = BoxLayout(orientation='vertical', spacing=15, padding=20)
        
        popup_layout.add_widget(Label(
            text='ЧАС НАГАДУВАННЯ!',
            font_size=22,
            color=(0.3, 0.5, 0.7, 1),
            bold=True
        ))
        
        popup_layout.add_widget(Label(
            text=reminder['title'],
            font_size=18,
            text_size=(400, None),
            halign='center',
            color=(0.2, 0.3, 0.4, 1)
        ))
        
        datetime_str = f"{reminder.get('date', '')} {reminder.get('time', '')}"
        popup_layout.add_widget(Label(
            text=datetime_str,
            font_size=14,
            color=(0.4, 0.5, 0.6, 1)
        ))
        
        ok_btn = Button(
            text='Зрозуміло',
            size_hint_y=None,
            height=50,
            background_color=(0.4, 0.6, 0.85, 1),
            font_size=16
        )
        
        popup = Popup(
            title='Нагадування',
            content=popup_layout,
            size_hint=(0.9, 0.6),
            auto_dismiss=False
        )
        
        ok_btn.bind(on_press=popup.dismiss)
        popup_layout.add_widget(ok_btn)
        popup.open()
    
    def save_reminders(self):
        """Зберігає нагадування"""
        try:
            with open('reminders.json', 'w', encoding='utf-8') as f:
                json.dump(self.reminders, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Помилка збереження: {e}")
    
    def load_reminders(self):
        """Завантажує нагадування"""
        try:
            if os.path.exists('reminders.json'):
                with open('reminders.json', 'r', encoding='utf-8') as f:
                    self.reminders = json.load(f)
                    self.cleanup_old_reminders()
        except Exception as e:
            print(f"Помилка завантаження: {e}")
            self.reminders = []
    
    def cleanup_old_reminders(self):
        """Видаляє старі нагадування"""
        now = datetime.now()
        valid_reminders = []
        
        for reminder in self.reminders:
            try:
                if 'datetime' in reminder:
                    reminder_datetime = datetime.fromisoformat(reminder['datetime'])
                    if reminder_datetime > now:
                        valid_reminders.append(reminder)
            except:
                continue
        
        if len(valid_reminders) != len(self.reminders):
            self.reminders = valid_reminders
            self.save_reminders()

if __name__ == "__main__":
    CalendarApp().run()

