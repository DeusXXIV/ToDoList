import tkinter as tk
from tkinter import messagebox, simpledialog
from tkinter import ttk
import sqlite3

# Database setup
def create_connection():
    conn = sqlite3.connect('todo_list.db')
    return conn

def create_tables():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS task_lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            list_name TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            completed BOOLEAN NOT NULL CHECK (completed IN (0, 1)),
            list_id INTEGER,
            FOREIGN KEY (list_id) REFERENCES task_lists (id)
        )
    ''')
    conn.commit()
    conn.close()

def update_database_schema():
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            ALTER TABLE tasks ADD COLUMN list_id INTEGER
        ''')
        conn.commit()
    except sqlite3.OperationalError:
        # Column might already exist
        pass
    conn.close()

def add_task_list(list_name):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO task_lists (list_name) VALUES (?)', (list_name,))
    conn.commit()
    conn.close()

def fetch_task_lists():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, list_name FROM task_lists')
    task_lists = cursor.fetchall()
    conn.close()
    return task_lists

def add_task_to_db(task, list_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO tasks (task, completed, list_id) VALUES (?, ?, ?)', (task, 0, list_id))
    conn.commit()
    conn.close()

def remove_task_from_db(task_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()

def mark_task_completed(task_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE tasks SET completed = 1 WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()

def fetch_tasks(list_id, completed=None):
    conn = create_connection()
    cursor = conn.cursor()
    query = 'SELECT id, task, completed FROM tasks WHERE list_id = ?'
    params = [list_id]
    if completed is not None:
        query += ' AND completed = ?'
        params.append(completed)
    cursor.execute(query, params)
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def add_task():
    task = entry_task.get()
    selected_list_id = combo_task_lists.get()
    if task and selected_list_id:
        list_id = int(selected_list_id.split(":")[0].strip())  # Extract list ID, strip any extra whitespace
        add_task_to_db(task, list_id)
        refresh_tasks()
        entry_task.delete(0, tk.END)
    else:
        messagebox.showwarning("Warning", "You must enter a task and select a task list.")

def remove_task():
    try:
        selected_task_index = listbox_ongoing_tasks.curselection()
        if selected_task_index:
            task_description = listbox_ongoing_tasks.get(selected_task_index[0])
            task_id = ongoing_tasks_map[task_description]  # Get task ID from mapping
            remove_task_from_db(task_id)
            refresh_tasks()
        else:
            selected_task_index = listbox_completed_tasks.curselection()
            if selected_task_index:
                task_description = listbox_completed_tasks.get(selected_task_index[0])
                task_id = completed_tasks_map[task_description]  # Get task ID from mapping
                remove_task_from_db(task_id)
                refresh_tasks()
            else:
                messagebox.showwarning("Warning", "You must select a task to remove.")
    except KeyError:
        messagebox.showwarning("Warning", "Selected task not found.")

def mark_completed():
    try:
        selected_task_index = listbox_ongoing_tasks.curselection()
        if selected_task_index:
            task_description = listbox_ongoing_tasks.get(selected_task_index[0])
            task_id = ongoing_tasks_map[task_description]  # Get task ID from mapping
            mark_task_completed(task_id)
            refresh_tasks()
        else:
            messagebox.showwarning("Warning", "You must select a task to mark as completed.")
    except KeyError:
        messagebox.showwarning("Warning", "Selected task not found.")

def refresh_tasks():
    selected_list = combo_task_lists.get()
    if selected_list:
        list_id = int(selected_list.split(":")[0].strip())  # Extract list ID, strip any extra whitespace
        ongoing_tasks = fetch_tasks(list_id, completed=0)
        completed_tasks = fetch_tasks(list_id, completed=1)

        listbox_ongoing_tasks.delete(0, tk.END)
        listbox_completed_tasks.delete(0, tk.END)

        # Maintain task description to ID mapping
        global ongoing_tasks_map
        global completed_tasks_map
        ongoing_tasks_map = {}
        completed_tasks_map = {}

        for task in ongoing_tasks:
            listbox_ongoing_tasks.insert(tk.END, task[1])  # Insert only task description
            ongoing_tasks_map[task[1]] = task[0]  # Map description to ID

        for task in completed_tasks:
            listbox_completed_tasks.insert(tk.END, task[1])  # Insert only task description
            completed_tasks_map[task[1]] = task[0]  # Map description to ID

def load_task_lists():
    task_lists = fetch_task_lists()
    combo_task_lists['values'] = [f"{list_id}: {list_name}" for list_id, list_name in task_lists]  # Format as "ID: Name"
    if task_lists:
        combo_task_lists.current(0)
        refresh_tasks()

def create_task_list():
    list_name = simpledialog.askstring("Task List", "Enter the name of the new task list:")
    if list_name:
        add_task_list(list_name)
        load_task_lists()

# Main application setup
app = tk.Tk()
app.title("To-Do List with Database")

create_tables()  # Ensure the database tables exist
update_database_schema()  # Update the schema if needed

# Frame for task list management
frame_list_management = tk.Frame(app)
frame_list_management.pack(pady=10)

# Create task list button
button_create_list = tk.Button(frame_list_management, text="Create Task List", command=create_task_list)
button_create_list.pack(side=tk.LEFT, padx=10)

# Dropdown to select task list
combo_task_lists = ttk.Combobox(frame_list_management, width=40)
combo_task_lists.pack(side=tk.LEFT, padx=10)
combo_task_lists.bind('<<ComboboxSelected>>', lambda e: refresh_tasks())

# Frame for the task entry
frame_entry = tk.Frame(app)
frame_entry.pack(pady=10)

# Task entry field
entry_task = tk.Entry(frame_entry, width=40)
entry_task.pack(side=tk.LEFT, padx=10)

# Add task button
button_add = tk.Button(frame_entry, text="Add Task", command=add_task)
button_add.pack(side=tk.LEFT)

# Frame for the task lists
frame_lists = tk.Frame(app)
frame_lists.pack(pady=10)

# Grid layout for labels and listboxes
label_ongoing_tasks = tk.Label(frame_lists, text="Ongoing Tasks")
label_ongoing_tasks.grid(row=0, column=0, padx=10, pady=5, sticky='w')

label_completed_tasks = tk.Label(frame_lists, text="Completed Tasks")
label_completed_tasks.grid(row=0, column=1, padx=10, pady=5, sticky='w')

# Listbox for ongoing tasks
listbox_ongoing_tasks = tk.Listbox(frame_lists, width=50, height=10, selectmode=tk.SINGLE)
listbox_ongoing_tasks.grid(row=1, column=0, padx=10, pady=5)

# Listbox for completed tasks
listbox_completed_tasks = tk.Listbox(frame_lists, width=50, height=10, selectmode=tk.SINGLE)
listbox_completed_tasks.grid(row=1, column=1, padx=10, pady=5)

# Frame for the action buttons
frame_buttons = tk.Frame(app)
frame_buttons.pack(pady=10)

# Remove task button
button_remove = tk.Button(frame_buttons, text="Remove Task", command=remove_task)
button_remove.pack(side=tk.LEFT, padx=10)

# Mark completed button
button_completed = tk.Button(frame_buttons, text="Mark Completed", command=mark_completed)
button_completed.pack(side=tk.LEFT, padx=10)

# Load task lists and initial tasks
load_task_lists()

app.mainloop()







