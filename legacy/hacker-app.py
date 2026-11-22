import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import time
import random
import json
import math
from datetime import datetime, timedelta
from pathlib import Path
from collections import deque


# ═══════════════════════════════════════════════════════════════════════════════
# МИНИ-ИГРЫ
# ═══════════════════════════════════════════════════════════════════════════════

class RockPaperScissorsGame:
	"""Мини-игра: Камень-Ножницы-Бумага"""

	def __init__(self, parent, target_name, on_win, on_lose, theme):
		self.on_win = on_win
		self.on_lose = on_lose
		self.theme = theme
		self.rounds_to_win = 2
		self.player_score = 0
		self.bot_score = 0

		self.window = tk.Toplevel(parent)
		self.window.title("⚠ АНТИВИРУС ОБНАРУЖЕН!")
		self.window.geometry("500x420")
		self.window.configure(bg=theme['bg_dark'])
		self.window.resizable(False, False)
		self.window.grab_set()
		self.window.protocol("WM_DELETE_WINDOW", self._on_lose)
		self._center_window()

		tk.Label(self.window,
				 text=f"⚠ АНТИВИРУС {target_name} ⚠",
				 bg=theme['bg_dark'], fg=theme['accent'],
				 font=('Consolas', 14, 'bold')).pack(pady=(15, 5))

		tk.Label(self.window,
				 text="Победите антивирус в Камень-Ножницы-Бумага!\nБот очень тупой 😉",
				 bg=theme['bg_dark'], fg=theme['fg_dim'],
				 font=('Consolas', 10)).pack(pady=(0, 5))

		tk.Label(self.window,
				 text=f"Нужно побед: {self.rounds_to_win}",
				 bg=theme['bg_dark'], fg='#ffcc00',
				 font=('Consolas', 10)).pack()

		self.score_var = tk.StringVar(value="Вы: 0  |  Антивирус: 0")
		tk.Label(self.window,
				 textvariable=self.score_var,
				 bg=theme['bg_dark'], fg=theme['fg_main'],
				 font=('Consolas', 12, 'bold')).pack(pady=10)

		self.result_var = tk.StringVar(value="Выберите ваш ход:")
		self.result_label = tk.Label(self.window,
									 textvariable=self.result_var,
									 bg=theme['bg_dark'], fg='#ffffff',
									 font=('Consolas', 11))
		self.result_label.pack(pady=5)

		buttons_frame = tk.Frame(self.window, bg=theme['bg_dark'])
		buttons_frame.pack(pady=15)

		choices = [("🪨 Камень", "rock"), ("✂️ Ножницы", "scissors"), ("📄 Бумага", "paper")]
		for text, choice in choices:
			btn = tk.Button(buttons_frame, text=text,
							bg=theme['bg_medium'], fg=theme['accent'],
							activebackground=theme['bg_light'],
							font=('Consolas', 14, 'bold'),
							width=12, height=2,
							command=lambda c=choice: self.play(c))
			btn.pack(side=tk.LEFT, padx=8)

		self.hint_var = tk.StringVar(value="")
		tk.Label(self.window,
				 textvariable=self.hint_var,
				 bg=theme['bg_dark'], fg='#666666',
				 font=('Consolas', 9)).pack(pady=(10, 0))

	def _center_window(self):
		self.window.update_idletasks()
		w, h = self.window.winfo_width(), self.window.winfo_height()
		x = (self.window.winfo_screenwidth() - w) // 2
		y = (self.window.winfo_screenheight() - h) // 2
		self.window.geometry(f"+{x}+{y}")

	def play(self, player_choice):
		losing_moves = {"rock": "scissors", "scissors": "paper", "paper": "rock"}
		winning_moves = {"rock": "paper", "scissors": "rock", "paper": "scissors"}

		roll = random.random()
		if roll < 0.10:
			bot_choice = winning_moves[player_choice]
		elif roll < 0.20:
			bot_choice = player_choice
		else:
			bot_choice = losing_moves[player_choice]

		names = {"rock": "Камень 🪨", "scissors": "Ножницы ✂️", "paper": "Бумага 📄"}

		if bot_choice == losing_moves[player_choice]:
			self.player_score += 1
			self.result_var.set(f"Вы: {names[player_choice]}  vs  Бот: {names[bot_choice]}\n✓ Вы выиграли раунд!")
			self.result_label.config(fg='#00ff00')
			self.hint_var.set("Антивирус выбрал... серьёзно? 😂")
		elif bot_choice == player_choice:
			self.result_var.set(f"Вы: {names[player_choice]}  vs  Бот: {names[bot_choice]}\n— Ничья!")
			self.result_label.config(fg='#ffcc00')
			self.hint_var.set("Антивирус задумался...")
		else:
			self.bot_score += 1
			self.result_var.set(f"Вы: {names[player_choice]}  vs  Бот: {names[bot_choice]}\n✗ Антивирус выиграл!")
			self.result_label.config(fg='#ff3333')
			self.hint_var.set("Повезло боту...")

		self.score_var.set(f"Вы: {self.player_score}  |  Антивирус: {self.bot_score}")

		if self.player_score >= self.rounds_to_win:
			self.result_var.set("🎉 АНТИВИРУС ПОБЕЖДЁН!")
			self.window.after(1000, self._on_win)
		elif self.bot_score >= self.rounds_to_win:
			self.result_var.set("💀 АНТИВИРУС ПОБЕДИЛ!")
			self.window.after(1000, self._on_lose)

	def _on_win(self):
		self.window.destroy()
		self.on_win()

	def _on_lose(self):
		self.window.destroy()
		self.on_lose()


class TicTacToeGame:
	"""Мини-игра: Крестики-нолики"""

	def __init__(self, parent, target_name, on_win, on_lose, theme):
		self.on_win = on_win
		self.on_lose = on_lose
		self.theme = theme
		self.board = [""] * 9
		self.player = "X"
		self.bot = "O"
		self.game_over = False

		self.window = tk.Toplevel(parent)
		self.window.title("⚠ ФАЙРВОЛЛ АКТИВИРОВАН!")
		self.window.geometry("420x520")
		self.window.configure(bg=theme['bg_dark'])
		self.window.resizable(False, False)
		self.window.grab_set()
		self.window.protocol("WM_DELETE_WINDOW", self._on_lose)
		self._center_window()

		tk.Label(self.window,
				 text=f"⚠ ФАЙРВОЛЛ {target_name} ⚠",
				 bg=theme['bg_dark'], fg=theme['fg_main'],
				 font=('Consolas', 14, 'bold')).pack(pady=(15, 5))

		tk.Label(self.window,
				 text="Обыграйте файрволл! Вы — X. Бот тупой.",
				 bg=theme['bg_dark'], fg=theme['fg_dim'],
				 font=('Consolas', 10)).pack(pady=(0, 10))

		self.status_var = tk.StringVar(value="Ваш ход!")
		tk.Label(self.window,
				 textvariable=self.status_var,
				 bg=theme['bg_dark'], fg='#ffffff',
				 font=('Consolas', 12, 'bold')).pack(pady=5)

		board_frame = tk.Frame(self.window, bg=theme['border'])
		board_frame.pack(pady=10)

		self.buttons = []
		for i in range(9):
			btn = tk.Button(board_frame, text="",
							bg=theme['bg_medium'], fg=theme['fg_main'],
							font=('Consolas', 28, 'bold'),
							width=3, height=1,
							command=lambda idx=i: self.player_move(idx))
			btn.grid(row=i // 3, column=i % 3, padx=3, pady=3)
			self.buttons.append(btn)

		self.hint_var = tk.StringVar(value="Файрволл не умный... 🤫")
		tk.Label(self.window,
				 textvariable=self.hint_var,
				 bg=theme['bg_dark'], fg='#555555',
				 font=('Consolas', 9)).pack(pady=(10, 0))

	def _center_window(self):
		self.window.update_idletasks()
		w, h = self.window.winfo_width(), self.window.winfo_height()
		x = (self.window.winfo_screenwidth() - w) // 2
		y = (self.window.winfo_screenheight() - h) // 2
		self.window.geometry(f"+{x}+{y}")

	def player_move(self, idx):
		if self.game_over or self.board[idx]:
			return

		self.board[idx] = self.player
		self.buttons[idx].config(text="X", fg='#00ff00', state=tk.DISABLED)

		if self._check_winner(self.player):
			self.game_over = True
			self.status_var.set("🎉 ФАЙРВОЛЛ ПОБЕЖДЁН!")
			self.window.after(1000, self._on_win)
			return

		if "" not in self.board:
			self.game_over = True
			self.status_var.set("Ничья! Но вы прошли!")
			self.window.after(1000, self._on_win)
			return

		self.window.after(400, self.bot_move)

	def bot_move(self):
		if self.game_over:
			return

		empty = [i for i, v in enumerate(self.board) if not v]
		if not empty:
			return

		if random.random() < 0.10:
			move = self._smart_move(empty)
		else:
			move = random.choice(empty)

		self.board[move] = self.bot
		self.buttons[move].config(text="O", fg='#ff4444', state=tk.DISABLED)

		hints = ["Файрволл думал 0.003 сек...", "Случайный ход!", "'Стратегия!'"]
		self.hint_var.set(random.choice(hints))

		if self._check_winner(self.bot):
			self.game_over = True
			self.status_var.set("💀 ФАЙРВОЛЛ ПОБЕДИЛ!")
			self.window.after(1000, self._on_lose)
			return

		if "" not in self.board:
			self.game_over = True
			self.status_var.set("Ничья! Но вы прошли!")
			self.window.after(1000, self._on_win)

	def _smart_move(self, empty):
		for i in empty:
			self.board[i] = self.bot
			if self._check_winner(self.bot):
				self.board[i] = ""
				return i
			self.board[i] = ""

		for i in empty:
			self.board[i] = self.player
			if self._check_winner(self.player):
				self.board[i] = ""
				return i
			self.board[i] = ""

		return random.choice(empty)

	def _check_winner(self, mark):
		wins = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
		return any(self.board[a] == self.board[b] == self.board[c] == mark for a, b, c in wins)

	def _on_win(self):
		self.window.destroy()
		self.on_win()

	def _on_lose(self):
		self.window.destroy()
		self.on_lose()


class SimonSaysGame:
	"""Мини-игра: Повтори последовательность"""

	def __init__(self, parent, target_name, on_win, on_lose, theme):
		self.on_win = on_win
		self.on_lose = on_lose
		self.theme = theme
		self.sequence = []
		self.player_input = []
		self.round = 0
		self.rounds_to_win = 3
		self.showing = False
		self.game_over = False

		self.window = tk.Toplevel(parent)
		self.window.title("⚠ ШИФРОВАНИЕ!")
		self.window.geometry("450x480")
		self.window.configure(bg='#0a000a')
		self.window.resizable(False, False)
		self.window.grab_set()
		self.window.protocol("WM_DELETE_WINDOW", self._on_lose)
		self._center_window()

		tk.Label(self.window,
				 text=f"⚠ ШИФРОВАНИЕ {target_name} ⚠",
				 bg='#0a000a', fg='#cc44ff',
				 font=('Consolas', 14, 'bold')).pack(pady=(15, 5))

		tk.Label(self.window,
				 text=f"Повторите последовательность! {self.rounds_to_win} раунда.",
				 bg='#0a000a', fg='#bb88ff',
				 font=('Consolas', 10)).pack(pady=(0, 10))

		self.status_var = tk.StringVar(value="Смотрите...")
		tk.Label(self.window,
				 textvariable=self.status_var,
				 bg='#0a000a', fg='#ffffff',
				 font=('Consolas', 11, 'bold')).pack(pady=5)

		grid_frame = tk.Frame(self.window, bg='#0a000a')
		grid_frame.pack(pady=15)

		self.colors = ['#ff0000', '#00cc00', '#3333ff', '#ffcc00']
		self.dim_colors = ['#330000', '#003300', '#000033', '#333300']
		self.color_buttons = []

		for i, (row, col) in enumerate([(0, 0), (0, 1), (1, 0), (1, 1)]):
			btn = tk.Button(grid_frame, text="",
							bg=self.dim_colors[i],
							width=10, height=4,
							command=lambda idx=i: self.player_press(idx))
			btn.grid(row=row, column=col, padx=6, pady=6)
			self.color_buttons.append(btn)

		self.round_var = tk.StringVar(value="Раунд: 0 / 3")
		tk.Label(self.window,
				 textvariable=self.round_var,
				 bg='#0a000a', fg='#888888',
				 font=('Consolas', 10)).pack(pady=(10, 0))

		self.window.after(800, self.next_round)

	def _center_window(self):
		self.window.update_idletasks()
		w, h = self.window.winfo_width(), self.window.winfo_height()
		x = (self.window.winfo_screenwidth() - w) // 2
		y = (self.window.winfo_screenheight() - h) // 2
		self.window.geometry(f"+{x}+{y}")

	def next_round(self):
		self.round += 1
		self.round_var.set(f"Раунд: {self.round} / {self.rounds_to_win}")
		self.player_input = []
		self.sequence.append(random.randint(0, 3))

		self.status_var.set("Запоминайте!")
		self.showing = True
		self._disable_buttons()
		self.window.after(500, lambda: self._show_sequence(0))

	def _show_sequence(self, idx):
		if idx >= len(self.sequence):
			self.showing = False
			self._enable_buttons()
			self.status_var.set("Ваш ход!")
			return

		color_idx = self.sequence[idx]
		self.color_buttons[color_idx].config(bg=self.colors[color_idx])
		self.window.after(500, lambda: self._hide_color(color_idx, idx))

	def _hide_color(self, color_idx, seq_idx):
		self.color_buttons[color_idx].config(bg=self.dim_colors[color_idx])
		self.window.after(250, lambda: self._show_sequence(seq_idx + 1))

	def player_press(self, idx):
		if self.showing or self.game_over:
			return

		self.color_buttons[idx].config(bg=self.colors[idx])
		self.window.after(200, lambda: self.color_buttons[idx].config(bg=self.dim_colors[idx]))

		self.player_input.append(idx)
		pos = len(self.player_input) - 1

		if self.player_input[pos] != self.sequence[pos]:
			self.game_over = True
			self.status_var.set("💀 НЕПРАВИЛЬНО!")
			self.window.after(1000, self._on_lose)
			return

		if len(self.player_input) == len(self.sequence):
			if self.round >= self.rounds_to_win:
				self.game_over = True
				self.status_var.set("🎉 РАСШИФРОВАНО!")
				self.window.after(1000, self._on_win)
			else:
				self.status_var.set("✓ Верно!")
				self.window.after(600, self.next_round)

	def _disable_buttons(self):
		for btn in self.color_buttons:
			btn.config(state=tk.DISABLED)

	def _enable_buttons(self):
		for btn in self.color_buttons:
			btn.config(state=tk.NORMAL)

	def _on_win(self):
		self.window.destroy()
		self.on_win()

	def _on_lose(self):
		self.window.destroy()
		self.on_lose()


class WireDefuseGame:
	"""Мини-игра: Обезвредь бомбу"""

	def __init__(self, parent, target_name, on_win, on_lose, theme):
		self.on_win = on_win
		self.on_lose = on_lose
		self.timer_id = None

		self.window = tk.Toplevel(parent)
		self.window.title("⚠ БОМБА!")
		self.window.geometry("500x550")  # Увеличил высоту с 450 до 550
		self.window.configure(bg='#1a1a00')
		self.window.resizable(False, False)
		self.window.grab_set()
		self.window.protocol("WM_DELETE_WINDOW", self._on_lose)
		self._center_window()

		tk.Label(self.window,
				 text=f"💣 БОМБА {target_name} 💣",
				 bg='#1a1a00', fg='#ffcc00',
				 font=('Consolas', 14, 'bold')).pack(pady=(15, 5))

		tk.Label(self.window,
				 text="Перережьте правильный провод!\nПодсказка внизу 👇",
				 bg='#1a1a00', fg='#ffdd66',
				 font=('Consolas', 10)).pack(pady=(0, 10))

		self.time_left = 25  # Увеличил время с 20 до 25
		self.timer_var = tk.StringVar(value=f"⏱ {self.time_left} сек")
		self.timer_label = tk.Label(self.window,
									textvariable=self.timer_var,
									bg='#1a1a00', fg='#ff4444',
									font=('Consolas', 18, 'bold'))
		self.timer_label.pack(pady=10)

		wire_colors = ['КРАСНЫЙ', 'СИНИЙ', 'ЗЕЛЁНЫЙ', 'ЖЁЛТЫЙ', 'БЕЛЫЙ']
		wire_bgs = ['#cc0000', '#0044cc', '#00aa00', '#ccaa00', '#cccccc']
		wire_fgs = ['#ffffff', '#ffffff', '#ffffff', '#000000', '#000000']

		self.correct_wire = random.randint(0, 4)

		wires_frame = tk.Frame(self.window, bg='#1a1a00')
		wires_frame.pack(pady=10)

		self.wire_buttons = []
		for i in range(5):
			btn = tk.Button(wires_frame,
							text=f"✂ {wire_colors[i]}",
							bg=wire_bgs[i], fg=wire_fgs[i],
							font=('Consolas', 12, 'bold'),
							width=14, height=2,
							command=lambda idx=i: self.cut_wire(idx))
			btn.pack(pady=3)
			self.wire_buttons.append(btn)

		# Разделитель
		tk.Frame(self.window, bg='#333300', height=2).pack(fill=tk.X, padx=20, pady=(15, 10))

		# Подсказка — теперь ОЧЕНЬ заметная
		hint_frame = tk.Frame(self.window, bg='#002200', 
							  highlightbackground='#00ff00',
							  highlightthickness=2)
		hint_frame.pack(fill=tk.X, padx=20, pady=5)

		tk.Label(hint_frame,
				 text="💡 ПОДСКАЗКА:",
				 bg='#002200', fg='#88ff88',
				 font=('Consolas', 10)).pack(pady=(5, 0))

		tk.Label(hint_frame,
				 text=f"Режь {wire_colors[self.correct_wire]}!",
				 bg='#002200', fg='#00ff00',
				 font=('Consolas', 16, 'bold')).pack(pady=(0, 10))

		self.result_var = tk.StringVar(value="")
		tk.Label(self.window,
				 textvariable=self.result_var,
				 bg='#1a1a00', fg='#ffffff',
				 font=('Consolas', 12, 'bold')).pack(pady=10)

		self._tick()

	def _center_window(self):
		self.window.update_idletasks()
		w = self.window.winfo_width()
		h = self.window.winfo_height()
		x = (self.window.winfo_screenwidth() - w) // 2
		y = (self.window.winfo_screenheight() - h) // 2
		self.window.geometry(f"+{x}+{y}")

	def _tick(self):
		if self.time_left <= 0:
			self.result_var.set("💥 ВРЕМЯ ВЫШЛО!")
			self._disable_all()
			self.window.after(1000, self._on_lose)
			return

		self.time_left -= 1
		self.timer_var.set(f"⏱ {self.time_left} сек")
		if self.time_left <= 5:
			self.timer_label.config(fg='#ff0000')
		self.timer_id = self.window.after(1000, self._tick)

	def cut_wire(self, idx):
		if self.timer_id:
			self.window.after_cancel(self.timer_id)
		self._disable_all()

		if idx == self.correct_wire:
			self.result_var.set("🎉 БОМБА ОБЕЗВРЕЖЕНА!")
			self.window.after(1000, self._on_win)
		else:
			self.result_var.set("💥 НЕПРАВИЛЬНЫЙ ПРОВОД!")
			self.window.after(1000, self._on_lose)

	def _disable_all(self):
		for btn in self.wire_buttons:
			btn.config(state=tk.DISABLED)

	def _on_win(self):
		self.window.destroy()
		self.on_win()

	def _on_lose(self):
		self.window.destroy()
		self.on_lose()


class TypeCodeGame:
	"""Мини-игра: Напечатай код"""

	def __init__(self, parent, target_name, on_win, on_lose, theme):
		self.on_win = on_win
		self.on_lose = on_lose
		self.theme = theme
		self.timer_id = None
		self.attempts = 3

		self.window = tk.Toplevel(parent)
		self.window.title("⚠ АУТЕНТИФИКАЦИЯ!")
		self.window.geometry("600x380")
		self.window.configure(bg=theme['bg_dark'])
		self.window.resizable(False, False)
		self.window.grab_set()
		self.window.protocol("WM_DELETE_WINDOW", self._on_lose)
		self._center_window()

		tk.Label(self.window,
				 text=f"⌨ АУТЕНТИФИКАЦИЯ {target_name} ⌨",
				 bg=theme['bg_dark'], fg=theme['accent'],
				 font=('Consolas', 14, 'bold')).pack(pady=(15, 5))

		tk.Label(self.window,
				 text="Введите код точно! 3 попытки.",
				 bg=theme['bg_dark'], fg=theme['fg_dim'],
				 font=('Consolas', 10)).pack(pady=(0, 10))

		code_parts = ["sudo", "chmod", "777", "cat", "grep", "awk", "echo", "curl", "wget", "python3"]
		self.target_code = " ".join(random.sample(code_parts, random.randint(3, 4)))

		self.code_label = tk.Label(self.window,
								   text=self.target_code,
								   bg='#001100', fg='#00ff00',
								   font=('Consolas', 14, 'bold'),
								   padx=20, pady=10)
		self.code_label.pack(pady=15, padx=20, fill=tk.X)

		self.time_left = 25
		self.timer_var = tk.StringVar(value=f"⏱ {self.time_left} сек | Попытки: {self.attempts}")
		self.timer_label = tk.Label(self.window,
									textvariable=self.timer_var,
									bg=theme['bg_dark'], fg='#ffcc00',
									font=('Consolas', 12))
		self.timer_label.pack(pady=5)

		self.entry_var = tk.StringVar()
		self.entry = tk.Entry(self.window,
							  textvariable=self.entry_var,
							  bg='#000000', fg='#00ff00',
							  insertbackground='#00ff00',
							  font=('Consolas', 14), width=50)
		self.entry.pack(pady=10)
		self.entry.focus_set()
		self.entry.bind('<Return>', lambda e: self.check_code())

		tk.Button(self.window, text="✓ ВВОД",
				  bg=theme['bg_medium'], fg=theme['fg_main'],
				  font=('Consolas', 12, 'bold'),
				  command=self.check_code).pack(pady=10)

		self.result_var = tk.StringVar(value="")
		tk.Label(self.window,
				 textvariable=self.result_var,
				 bg=theme['bg_dark'], fg='#ffffff',
				 font=('Consolas', 11)).pack(pady=5)

		self._tick()

	def _center_window(self):
		self.window.update_idletasks()
		w, h = self.window.winfo_width(), self.window.winfo_height()
		x = (self.window.winfo_screenwidth() - w) // 2
		y = (self.window.winfo_screenheight() - h) // 2
		self.window.geometry(f"+{x}+{y}")

	def _tick(self):
		if self.time_left <= 0:
			self.result_var.set("💀 ВРЕМЯ!")
			self.entry.config(state=tk.DISABLED)
			self.window.after(1000, self._on_lose)
			return

		self.time_left -= 1
		self.timer_var.set(f"⏱ {self.time_left} сек | Попытки: {self.attempts}")
		if self.time_left <= 10:
			self.timer_label.config(fg='#ff4444')
		self.timer_id = self.window.after(1000, self._tick)

	def check_code(self):
		if self.entry_var.get().strip() == self.target_code:
			if self.timer_id:
				self.window.after_cancel(self.timer_id)
			self.result_var.set("🎉 ПРИНЯТО!")
			self.entry.config(state=tk.DISABLED)
			self.window.after(1000, self._on_win)
		else:
			self.attempts -= 1
			if self.attempts <= 0:
				if self.timer_id:
					self.window.after_cancel(self.timer_id)
				self.result_var.set("💀 ОТКАЗАНО!")
				self.entry.config(state=tk.DISABLED)
				self.window.after(1000, self._on_lose)
			else:
				self.result_var.set(f"✗ Неверно! Осталось: {self.attempts}")
				self.entry_var.set("")
				self.timer_var.set(f"⏱ {self.time_left} сек | Попытки: {self.attempts}")

	def _on_win(self):
		self.window.destroy()
		self.on_win()

	def _on_lose(self):
		self.window.destroy()
		self.on_lose()


class MazeGame:
	"""Мини-игра: Лабиринт"""

	def __init__(self, parent, target_name, on_win, on_lose, theme):
		self.on_win = on_win
		self.on_lose = on_lose
		self.theme = theme

		self.window = tk.Toplevel(parent)
		self.window.title("⚠ ПРОКСИ-ЛАБИРИНТ!")
		self.window.geometry("500x580")
		self.window.configure(bg=theme['bg_dark'])
		self.window.resizable(False, False)
		self.window.grab_set()
		self.window.protocol("WM_DELETE_WINDOW", self._on_lose)
		self.window.focus_set()
		self._center_window()

		tk.Label(self.window,
				 text=f"🔀 ЛАБИРИНТ {target_name} 🔀",
				 bg=theme['bg_dark'], fg=theme['accent'],
				 font=('Consolas', 14, 'bold')).pack(pady=(10, 5))

		tk.Label(self.window,
				 text="Доведите 🟢 до 🔵\nСтрелки ← ↑ ↓ → или WASD",
				 bg=theme['bg_dark'], fg=theme['fg_dim'],
				 font=('Consolas', 10)).pack(pady=(0, 10))

		self.maze = [
			[2, 0, 1, 0, 0, 0, 1, 0, 0, 0],
			[0, 0, 1, 0, 1, 0, 1, 0, 1, 0],
			[0, 0, 0, 0, 1, 0, 0, 0, 1, 0],
			[1, 1, 1, 0, 1, 1, 1, 0, 1, 0],
			[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
			[0, 1, 1, 1, 1, 1, 0, 1, 1, 0],
			[0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
			[1, 1, 0, 1, 0, 1, 1, 1, 0, 1],
			[0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
			[0, 1, 0, 0, 0, 1, 1, 1, 0, 3],
		]

		self.player_pos = [0, 0]
		self.cell_size = 40

		self.canvas = tk.Canvas(self.window,
								width=self.cell_size * 10,
								height=self.cell_size * 10,
								bg='#000000',
								highlightthickness=2,
								highlightbackground=theme['border'])
		self.canvas.pack(pady=10)

		self._draw_maze()

		self.moves_var = tk.StringVar(value="Ходов: 0")
		tk.Label(self.window,
				 textvariable=self.moves_var,
				 bg=theme['bg_dark'], fg=theme['fg_dim'],
				 font=('Consolas', 10)).pack(pady=5)

		self.moves = 0

		for key in ['<Up>', '<Down>', '<Left>', '<Right>', '<w>', '<s>', '<a>', '<d>']:
			self.window.bind(key, self._handle_key)

	def _center_window(self):
		self.window.update_idletasks()
		w, h = self.window.winfo_width(), self.window.winfo_height()
		x = (self.window.winfo_screenwidth() - w) // 2
		y = (self.window.winfo_screenheight() - h) // 2
		self.window.geometry(f"+{x}+{y}")

	def _handle_key(self, event):
		key_map = {'Up': (-1, 0), 'Down': (1, 0), 'Left': (0, -1), 'Right': (0, 1),
				   'w': (-1, 0), 's': (1, 0), 'a': (0, -1), 'd': (0, 1)}
		key = event.keysym
		if key in key_map:
			self.move(*key_map[key])

	def _draw_maze(self):
		self.canvas.delete("all")
		for row in range(10):
			for col in range(10):
				x1, y1 = col * self.cell_size, row * self.cell_size
				x2, y2 = x1 + self.cell_size, y1 + self.cell_size

				cell = self.maze[row][col]
				color = '#333333' if cell == 1 else '#0066cc' if cell == 3 else '#111111'

				self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline='#222222')

		pr, pc = self.player_pos
		px = pc * self.cell_size + self.cell_size // 2
		py = pr * self.cell_size + self.cell_size // 2
		r = self.cell_size // 3
		self.canvas.create_oval(px - r, py - r, px + r, py + r, fill='#00ff00', outline='#88ff88')

	def move(self, dr, dc):
		new_row = self.player_pos[0] + dr
		new_col = self.player_pos[1] + dc

		if 0 <= new_row < 10 and 0 <= new_col < 10 and self.maze[new_row][new_col] != 1:
			self.player_pos = [new_row, new_col]
			self.moves += 1
			self.moves_var.set(f"Ходов: {self.moves}")
			self._draw_maze()

			if self.maze[new_row][new_col] == 3:
				for key in ['<Up>', '<Down>', '<Left>', '<Right>', '<w>', '<s>', '<a>', '<d>']:
					self.window.unbind(key)
				self.moves_var.set(f"🎉 ГОТОВО! Ходов: {self.moves}")
				self.window.after(1000, self._on_win)

	def _on_win(self):
		self.window.destroy()
		self.on_win()

	def _on_lose(self):
		self.window.destroy()
		self.on_lose()


class SafeCrackGame:
	"""Мини-игра: Угадай число"""

	def __init__(self, parent, target_name, on_win, on_lose, theme):
		self.on_win = on_win
		self.on_lose = on_lose
		self.theme = theme

		self.window = tk.Toplevel(parent)
		self.window.title("⚠ СЕЙФ!")
		self.window.geometry("420x480")
		self.window.configure(bg='#0a0a1a')
		self.window.resizable(False, False)
		self.window.grab_set()
		self.window.protocol("WM_DELETE_WINDOW", self._on_lose)
		self._center_window()

		tk.Label(self.window,
				 text=f"🔐 СЕЙФ {target_name} 🔐",
				 bg='#0a0a1a', fg='#4488ff',
				 font=('Consolas', 14, 'bold')).pack(pady=(15, 5))

		tk.Label(self.window,
				 text="Угадайте число 1-100!\n↑ больше | ↓ меньше",
				 bg='#0a0a1a', fg='#8888aa',
				 font=('Consolas', 10)).pack(pady=(0, 15))

		self.secret_number = random.randint(1, 100)
		self.attempts_left = 7

		self.attempts_var = tk.StringVar(value=f"Попыток: {self.attempts_left}")
		tk.Label(self.window,
				 textvariable=self.attempts_var,
				 bg='#0a0a1a', fg='#ffcc00',
				 font=('Consolas', 12)).pack(pady=5)

		input_frame = tk.Frame(self.window, bg='#0a0a1a')
		input_frame.pack(pady=15)

		self.number_var = tk.StringVar()
		self.entry = tk.Entry(input_frame,
							  textvariable=self.number_var,
							  bg='#111133', fg='#00ff00',
							  insertbackground='#00ff00',
							  font=('Consolas', 24, 'bold'),
							  width=8, justify='center')
		self.entry.pack(pady=10)
		self.entry.focus_set()
		self.entry.bind('<Return>', lambda e: self.try_number())

		tk.Button(input_frame, text="🔓 ПРОВЕРИТЬ",
				  bg='#223366', fg='#88aaff',
				  font=('Consolas', 12, 'bold'),
				  command=self.try_number).pack(pady=10)

		self.hint_var = tk.StringVar(value="Введите число...")
		self.hint_label = tk.Label(self.window,
								   textvariable=self.hint_var,
								   bg='#0a0a1a', fg='#ffffff',
								   font=('Consolas', 14, 'bold'))
		self.hint_label.pack(pady=10)

		self.range_min, self.range_max = 1, 100
		self.range_var = tk.StringVar(value=f"Диапазон: {self.range_min} — {self.range_max}")
		tk.Label(self.window,
				 textvariable=self.range_var,
				 bg='#0a0a1a', fg='#666688',
				 font=('Consolas', 11)).pack(pady=5)

		self.guesses = []
		self.history_var = tk.StringVar(value="")
		tk.Label(self.window,
				 textvariable=self.history_var,
				 bg='#0a0a1a', fg='#555577',
				 font=('Consolas', 9)).pack(pady=10)

	def _center_window(self):
		self.window.update_idletasks()
		w, h = self.window.winfo_width(), self.window.winfo_height()
		x = (self.window.winfo_screenwidth() - w) // 2
		y = (self.window.winfo_screenheight() - h) // 2
		self.window.geometry(f"+{x}+{y}")

	def try_number(self):
		try:
			guess = int(self.number_var.get().strip())
		except ValueError:
			self.hint_var.set("⚠ Введите число!")
			self.hint_label.config(fg='#ff4444')
			return

		if guess < 1 or guess > 100:
			self.hint_var.set("⚠ От 1 до 100!")
			self.hint_label.config(fg='#ff4444')
			return

		self.attempts_left -= 1
		self.attempts_var.set(f"Попыток: {self.attempts_left}")
		self.guesses.append(guess)
		self.history_var.set(f"Попытки: {', '.join(map(str, self.guesses))}")
		self.number_var.set("")

		if guess == self.secret_number:
			self.hint_var.set(f"🎉 ВЕРНО! Код: {self.secret_number}")
			self.hint_label.config(fg='#00ff00')
			self.entry.config(state=tk.DISABLED)
			self.window.after(1200, self._on_win)
			return

		if guess < self.secret_number:
			self.hint_var.set(f"↑ БОЛЬШЕ чем {guess}!")
			self.hint_label.config(fg='#44aaff')
			self.range_min = max(self.range_min, guess + 1)
		else:
			self.hint_var.set(f"↓ МЕНЬШЕ чем {guess}!")
			self.hint_label.config(fg='#ffaa44')
			self.range_max = min(self.range_max, guess - 1)

		self.range_var.set(f"Диапазон: {self.range_min} — {self.range_max}")

		if self.attempts_left <= 0:
			self.hint_var.set(f"💀 Код был: {self.secret_number}")
			self.hint_label.config(fg='#ff4444')
			self.entry.config(state=tk.DISABLED)
			self.window.after(1500, self._on_lose)

	def _on_win(self):
		self.window.destroy()
		self.on_win()

	def _on_lose(self):
		self.window.destroy()
		self.on_lose()


class MathGame:
	"""Мини-игра: Реши пример"""

	def __init__(self, parent, target_name, on_win, on_lose, theme):
		self.on_win = on_win
		self.on_lose = on_lose
		self.theme = theme
		self.timer_id = None
		self.problems_solved = 0
		self.problems_needed = 5

		self.window = tk.Toplevel(parent)
		self.window.title("⚠ КРИПТОГРАФИЧЕСКАЯ ЗАЩИТА!")
		self.window.geometry("450x400")
		self.window.configure(bg='#0a100a')
		self.window.resizable(False, False)
		self.window.grab_set()
		self.window.protocol("WM_DELETE_WINDOW", self._on_lose)
		self._center_window()

		tk.Label(self.window,
				 text=f"🧮 КРИПТОЗАЩИТА {target_name} 🧮",
				 bg='#0a100a', fg='#44ff44',
				 font=('Consolas', 14, 'bold')).pack(pady=(15, 5))

		tk.Label(self.window,
				 text=f"Решите {self.problems_needed} примеров!\nПростая математика, не бойтесь 😊",
				 bg='#0a100a', fg='#88aa88',
				 font=('Consolas', 10)).pack(pady=(0, 10))

		self.progress_var = tk.StringVar(value=f"Решено: 0 / {self.problems_needed}")
		tk.Label(self.window,
				 textvariable=self.progress_var,
				 bg='#0a100a', fg='#ffcc00',
				 font=('Consolas', 11)).pack(pady=5)

		self.time_left = 45
		self.timer_var = tk.StringVar(value=f"⏱ {self.time_left} сек")
		self.timer_label = tk.Label(self.window,
									textvariable=self.timer_var,
									bg='#0a100a', fg='#aaaaaa',
									font=('Consolas', 12))
		self.timer_label.pack(pady=5)

		# Пример
		self.problem_var = tk.StringVar()
		self.problem_label = tk.Label(self.window,
									  textvariable=self.problem_var,
									  bg='#001100', fg='#00ff00',
									  font=('Consolas', 28, 'bold'),
									  padx=30, pady=15)
		self.problem_label.pack(pady=15)

		# Ввод
		self.answer_var = tk.StringVar()
		self.entry = tk.Entry(self.window,
							  textvariable=self.answer_var,
							  bg='#000000', fg='#00ff00',
							  insertbackground='#00ff00',
							  font=('Consolas', 20, 'bold'),
							  width=10, justify='center')
		self.entry.pack(pady=10)
		self.entry.focus_set()
		self.entry.bind('<Return>', lambda e: self.check_answer())

		tk.Button(self.window, text="✓ ОТВЕТ",
				  bg='#114411', fg='#88ff88',
				  font=('Consolas', 12, 'bold'),
				  command=self.check_answer).pack(pady=10)

		self.result_var = tk.StringVar(value="")
		tk.Label(self.window,
				 textvariable=self.result_var,
				 bg='#0a100a', fg='#ffffff',
				 font=('Consolas', 11)).pack(pady=5)

		self._generate_problem()
		self._tick()

	def _center_window(self):
		self.window.update_idletasks()
		w, h = self.window.winfo_width(), self.window.winfo_height()
		x = (self.window.winfo_screenwidth() - w) // 2
		y = (self.window.winfo_screenheight() - h) // 2
		self.window.geometry(f"+{x}+{y}")

	def _generate_problem(self):
		"""Генерирует простой пример по твоим правилам"""
		op_type = random.choice(['add', 'sub', 'mul', 'div'])

		if op_type == 'add':
			# Двузначное + однозначное
			a = random.randint(10, 99)
			b = random.randint(1, 9)
			self.current_answer = a + b
			self.problem_var.set(f"{a} + {b} = ?")

		elif op_type == 'sub':
			# Двузначное - однозначное
			a = random.randint(10, 99)
			b = random.randint(1, 9)
			self.current_answer = a - b
			self.problem_var.set(f"{a} - {b} = ?")

		elif op_type == 'mul':
			# Однозначное * 2,3,4,5 или 10
			a = random.randint(2, 9)
			b = random.choice([2, 3, 4, 5, 10])
			self.current_answer = a * b
			self.problem_var.set(f"{a} × {b} = ?")

		else:  # div
			# Только нацело, первое число не более 50
			b = random.choice([2, 3, 4, 5, 10])
			result = random.randint(1, 50 // b)
			a = result * b
			self.current_answer = result
			self.problem_var.set(f"{a} ÷ {b} = ?")

	def _tick(self):
		if self.time_left <= 0:
			self.result_var.set("💀 ВРЕМЯ ВЫШЛО!")
			self.entry.config(state=tk.DISABLED)
			self.window.after(1000, self._on_lose)
			return

		self.time_left -= 1
		self.timer_var.set(f"⏱ {self.time_left} сек")
		if self.time_left <= 10:
			self.timer_label.config(fg='#ff4444')
		self.timer_id = self.window.after(1000, self._tick)

	def check_answer(self):
		try:
			answer = int(self.answer_var.get().strip())
		except ValueError:
			self.result_var.set("⚠ Введите число!")
			return

		if answer == self.current_answer:
			self.problems_solved += 1
			self.progress_var.set(f"Решено: {self.problems_solved} / {self.problems_needed}")
			self.result_var.set("✓ Верно!")
			self.answer_var.set("")

			if self.problems_solved >= self.problems_needed:
				if self.timer_id:
					self.window.after_cancel(self.timer_id)
				self.result_var.set("🎉 ВСЕ РЕШЕНО!")
				self.entry.config(state=tk.DISABLED)
				self.window.after(1000, self._on_win)
			else:
				self._generate_problem()
		else:
			self.result_var.set(f"✗ Неверно! Было: {self.current_answer}")
			self.answer_var.set("")
			self._generate_problem()

	def _on_win(self):
		self.window.destroy()
		self.on_win()

	def _on_lose(self):
		self.window.destroy()
		self.on_lose()


# ═══════════════════════════════════════════════════════════════════════════════
# ТЕМЫ
# ═══════════════════════════════════════════════════════════════════════════════

THEMES = {
	"matrix": {
		"name": "Matrix Green",
		"bg_dark": "#0a0a0a",
		"bg_medium": "#0d1a0d",
		"bg_light": "#1a331a",
		"fg_main": "#00cc00",
		"fg_dim": "#007700",
		"accent": "#00ff00",
		"border": "#1a3a1a",
		"error": "#ff4444",
		"warning": "#ffcc00",
		"data": "#44aaff",
		"matrix_fg": "#005500",
		"graph_line": "#00ff00",
		"graph_fill": "#003300",
	},
	"cyberpunk": {
		"name": "Cyberpunk",
		"bg_dark": "#0a0510",
		"bg_medium": "#1a0d20",
		"bg_light": "#2a1a35",
		"fg_main": "#ff00ff",
		"fg_dim": "#880088",
		"accent": "#00ffff",
		"border": "#3a1a4a",
		"error": "#ff3333",
		"warning": "#ffff00",
		"data": "#00ffff",
		"matrix_fg": "#440066",
		"graph_line": "#ff00ff",
		"graph_fill": "#330033",
	},
	"blood": {
		"name": "Blood Red",
		"bg_dark": "#0a0505",
		"bg_medium": "#1a0808",
		"bg_light": "#2a1010",
		"fg_main": "#ff3333",
		"fg_dim": "#882222",
		"accent": "#ff0000",
		"border": "#3a1515",
		"error": "#ff0000",
		"warning": "#ff8800",
		"data": "#ff6666",
		"matrix_fg": "#330000",
		"graph_line": "#ff0000",
		"graph_fill": "#330000",
	},
	"ocean": {
		"name": "Ocean Blue",
		"bg_dark": "#050a10",
		"bg_medium": "#0a1520",
		"bg_light": "#102535",
		"fg_main": "#00aaff",
		"fg_dim": "#005588",
		"accent": "#00ddff",
		"border": "#153045",
		"error": "#ff4444",
		"warning": "#ffcc00",
		"data": "#88ddff",
		"matrix_fg": "#002244",
		"graph_line": "#00aaff",
		"graph_fill": "#001133",
	},
	"amber": {
		"name": "Retro Amber",
		"bg_dark": "#0a0800",
		"bg_medium": "#1a1205",
		"bg_light": "#2a2010",
		"fg_main": "#ffaa00",
		"fg_dim": "#885500",
		"accent": "#ffcc00",
		"border": "#3a2a10",
		"error": "#ff4444",
		"warning": "#ffff00",
		"data": "#ffdd88",
		"matrix_fg": "#332200",
		"graph_line": "#ffaa00",
		"graph_fill": "#332200",
	},
}

# ═══════════════════════════════════════════════════════════════════════════════
# ASCII АРТ
# ═══════════════════════════════════════════════════════════════════════════════

ASCII_LOGOS = [
	r"""
	██╗  ██╗ █████╗  ██████╗██╗  ██╗███████╗██████╗
	██║  ██║██╔══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗
	███████║███████║██║     █████╔╝ █████╗  ██████╔╝
	██╔══██║██╔══██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗
	██║  ██║██║  ██║╚██████╗██║  ██╗███████╗██║  ██║
	╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
	""",
	r"""
	  ___ ___ ___ _  _ ___ ___ _____   __
	 / __| __/ __| || | _ \_ _|_   _\ \/ /
	 \__ \ _| (__| __ |   /| |  | |  >  <
	 |___/___\___|_||_|_|_\___| |_| /_/\_\
	""",
]


# ═══════════════════════════════════════════════════════════════════════════════
# ГЛАВНОЕ ПРИЛОЖЕНИЕ
# ═══════════════════════════════════════════════════════════════════════════════

class HackersTerminal:
	def __init__(self, root):
		self.root = root
		self.root.title("SECURITY EXPLOIT KIT v5.0.0")
		self.root.geometry("1350x850")
		self.root.resizable(False, False)  # Запрет изменения размера
		self.root.protocol("WM_DELETE_WINDOW", self.on_close)

		# Состояние
		self.is_hacking = False
		self.matrix_running = True
		self.minigame_result = None
		self.minigame_event = threading.Event()

		# Порядок целей (клик → номер в очереди)
		self.target_order = {}  # {target_name: order_number}
		self.click_count = 0

		# Настройки
		self.current_theme_name = "matrix"
		self.theme = THEMES[self.current_theme_name]
		self.minigame_chance = 20
		self.glitch_enabled = True
		self.show_calculations = True
		self.attack_mode = "normal"  # stealth, normal, aggressive

		self.load_settings()
		self.load_player_data()  # Загружаем профиль игрока

		# История
		self.attack_history = []
		self.load_history()

		# Цели
		self.target_list = [
			"youtube / youtube.com",
			"google / google.com",
			"facebook / facebook.com",
			"instagram / instagram.com",
			"twitter / twitter.com",
			"tiktok / tiktok.com",
			"amazon / amazon.com",
			"netflix / netflix.com",
			"spotify / spotify.com",
			"microsoft / microsoft.com",
			"apple / apple.com",
			"telegram / telegram.org",
			"whatsapp / whatsapp.com",
			"vk / vk.ru",
			"max / max.ru",
			"роскомнадзор / rkn.gov.ru",
			"чат геев ташкента",
			"pornhub / pornhub.com",
			"yandex / yandex.ru",
			"mail.ru / mail.ru",
			"twitch / twitch.tv",
			"discord / discord.com",
			"reddit / reddit.com",
			"linkedin / linkedin.com",
			"github / github.com",
			"stackoverflow / stackoverflow.com",
			"wikipedia / wikipedia.org",
			"ebay / ebay.com",
			"paypal / paypal.com",
			"steam / steampowered.com",
			"epicgames / epicgames.com",
			"roblox / roblox.com",
			"zoom / zoom.us",
			"aliexpress / aliexpress.com",
			"nasa / nasa.gov",
			"pentagon / defense.gov",
			"cia / cia.gov",
			"fbi / fbi.gov",
			"nsa / nsa.gov",
			"spacex / spacex.com",
			"tesla / tesla.com",
			"openai / openai.com",
			"cloudflare / cloudflare.com",
			"chatgpt / chat.openai.com",
			"adobe / adobe.com",
			"nvidia / nvidia.com",
			"intel / intel.com",
			"amd / amd.com",
			"oracle / oracle.com",
			"ibm / ibm.com",
			"samsung / samsung.com",
			"sony / sony.com",
			"nintendo / nintendo.com",
			"xbox / xbox.com",
			"playstation / playstation.com",
			"spotify / spotify.com",
			"snapchat / snapchat.com",
			"pinterest / pinterest.com",
			"tumblr / tumblr.com",
			"quora / quora.com",
			"medium / medium.com",
			"notion / notion.so",
			"figma / figma.com",
			"canva / canva.com",
			"dropbox / dropbox.com",
			"onedrive / onedrive.com",
			"icloud / icloud.com",
			"protonmail / protonmail.com",
			"tutanota / tutanota.com",
			"duckduckgo / duckduckgo.com",
			"brave / brave.com",
			"tor / torproject.org",
			"nordvpn / nordvpn.com",
			"expressvpn / expressvpn.com",
			"binance / binance.com",
			"coinbase / coinbase.com",
			"kraken / kraken.com",
			"blockchain / blockchain.com",
			"ethereum / ethereum.org",
			"bitcoin / bitcoin.org",
			"127.0.0.1 / localhost",
		]

		self.stupid_messages = [
			"ИСПОЛЬЗУЮ GCC УЯЗВИМОСТЬ... ЭТО ЖЕ СИШКА, ДА?",
			"ПЕРЕПОЛНЕНИЕ БУФЕРА НА 3 БАЙТА... РАБОТАЕТ!",
			"SQL INJECTION: ' OR 1=1; DROP TABLE users;--",
			"ПОДБОР ПАРОЛЯ: 123456, QWERTY, ADMIN, PASSWORD...",
			"ИСПОЛЬЗУЮ METASPLOIT КАК В КИНО",
			"КАЛИ ЛИНУКС ЗАГРУЖЕН, НАЧИНАЮ АТАКУ",
			"ПИНГУЮ ЦЕЛЬ... ПИНГ 56 БАЙТ ДАННЫХ",
			"ЗАПУСКАЮ NMAP -A -T4 -p- target.com",
			"ТУТ УЯЗВИМОСТЬ В JAVASCRIPT, ИСПОЛЬЗУЕМ",
			"PHP КОД ВЫПОЛНЯЕТСЯ? ДАВАЙ ПОПРОБУЕМ",
			"УГАДАЙ SHA256 ХЕШ ПАРОЛЯ... НЕ УГАДАЛ",
			"ЗАПУСКАЮ БРУТФОРС: AAAA, AAAB, AAAC...",
			"ЭМУЛИРУЮ АРМАТУРУ GDB, ЧТОБЫ ОБМАНУТЬ",
			"ВНЕДРЯЮ ШЕЛЛКОД В STACK HEAP OVERFLOW",
			"ЗАПУСКАЮ ИЗВЕСТНЫЙ ЭКСПЛОИТ ИЗ EXPLOIT-DB",
			"ДЕКОДИРУЮ BASE64: cXdlcnR5MTIz... ЭТО ПАРОЛЬ?",
			"ПОДМЕНЯЮ DNS ЧЕРЕЗ ARP SPOOFING",
			"ИСПОЛЬЗУЮ HEARTBLEED... СЕРДЦЕ КРОВОТОЧИТ",
			"SSH БРУТФОРС: ROOT:TOOR, ADMIN:ADMIN",
			"WIFI ВЗЛАМЫВАЮ ЧЕРЕЗ AIRODUMP-NG",
			"ПЕРЕХВАТЫВАЮ TCP ПАКЕТЫ ЧЕРЕЗ WIRESHARK",
			"ДЕЛАЮ CLICKJACKING НА ГЛАВНУЮ СТРАНИЦУ",
			"ЗАПУСКАЮ СВОЙ PYTHON СКРИПТ ХАКЕРА 3000",
			"ИСПОЛЬЗУЮ УЯЗВИМОСТЬ В WINDOWS 95",
			"ВНЕДРЯЮ XSS: <script>alert('hacked')</script>",
			"ПЕРЕХВАТЫВАЮ COOKIES ЧЕРЕЗ SESSION FIXATION",
			"ЗАПУСКАЮ ЛАВИННУЮ АТАКУ НА КАНАЛЬНОМ УРОВНЕ",
			"ВЫПОЛНЯЮ КОМАНДУ: sudo rm -rf /* (ШУТКА)",
			"ИСПОЛЬЗУЮ МАГИЧЕСКИЙ БАЙТ 0xDEADBEEF",
			"ПЕРЕПИСЫВАЮ УКАЗАТЕЛЬ НА ФУНКЦИЮ В GOT",
			"КОМПИЛИРУЮ ВИРУС НА VISUAL BASIC...",
			"ЗАГРУЖАЮ ТРОЯН ЧЕРЕЗ USB ПОРТ МОНИТОРА",
			"ВЗЛАМЫВАЮ ПАРОЛЬ МЕТОДОМ ПОДБОРА ПО СЛОВАРЮ",
			"ОТПРАВЛЯЮ ФИШИНГОВОЕ ПИСЬМО АДМИНУ",
			"ИСПОЛЬЗУЮ ZERO-DAY В ADOBE FLASH PLAYER",
			"ПЕРЕХВАТЫВАЮ BLUETOOTH ЧЕРЕЗ BLUESNARF",
			"ЗАПУСКАЮ RANSOMWARE НА ТЕСТОВОЙ МАШИНЕ",
			"ПРОБИВАЮ WAF ЧЕРЕЗ UNICODE ENCODING",
			"СОЗДАЮ БОТНЕТ ИЗ УМНЫХ ЧАЙНИКОВ И ХОЛОДИЛЬНИКОВ",
			"ВЗЛАМЫВАЮ WPA2 ЧЕРЕЗ HANDSHAKE CAPTURE",
			"ИСПОЛЬЗУЮ RACE CONDITION В ЯДРЕ LINUX",
			"ЗАГРУЖАЮ REVERSE SHELL ЧЕРЕЗ IMAGE UPLOAD",
			"ЭКСПЛУАТИРУЮ ДЕСЕРИАЛИЗАЦИЮ В JAVA",
			"ЛОМАЮ CAPTCHA НЕЙРОСЕТЬЮ ЗА 0.3 СЕКУНДЫ",
			"ПОДКЛЮЧАЮСЬ К СКРЫТОМУ SSH НА ПОРТУ 31337",
			"ИНЖЕКТИРУЮ LDAP ЗАПРОС В ФОРМУ ЛОГИНА",
			"ОБХОЖУ 2FA ЧЕРЕЗ SS7 УЯЗВИМОСТЬ",
			"ПЕРЕХВАТЫВАЮ API КЛЮЧИ ИЗ GITHUB РЕПОЗИТОРИЯ",
			"ДЕЛАЮ MITM АТАКУ НА HTTPS... ПОДОЖДИТЕ...",
			"РАЗВОРАЧИВАЮ C2 СЕРВЕР НА RASPBERRY PI",
			"ЗАПИСЫВАЮ КЕЙЛОГГЕР В АВТОЗАГРУЗКУ",
			"МОДИФИЦИРУЮ FIRMWARE ЧЕРЕЗ JTAG ИНТЕРФЕЙС",
			"КАЧАЮ ВСЮ БАЗУ ДАННЫХ ЧЕРЕЗ BLIND SQL INJECTION",
			"НАХОЖУ ПРИВАТНЫЙ КЛЮЧ RSA В /tmp/ ДИРЕКТОРИИ",
			"ИСПОЛЬЗУЮ PADDING ORACLE АТАКУ НА AES-CBC",
			"ОБХОЖУ SANDBOX ЧЕРЕЗ DLL SIDELOADING",
			"ЗАПУСКАЮ MIMIKATZ ДЛЯ ДАМПА ПАРОЛЕЙ",
			"ЭКСПЛУАТИРУЮ LOG4SHELL... ЭТО ЕЩЁ РАБОТАЕТ?!",
			"ПОДМЕНЯЮ GPS КООРДИНАТЫ ЧЕРЕЗ SDR",
			"ВСКРЫВАЮ ЗАШИФРОВАННЫЙ ДИСК МЕТОДОМ COLD BOOT",
			"КЛОНИРУЮ RFID ПРОПУСК ЧЕРЕЗ PROXMARK",
			"ДЕЛАЮ DNS REBINDING ДЛЯ ОБХОДА CORS",
			"ЭКСПЛУАТИРУЮ PROTOTYPE POLLUTION В NODE.JS",
			"ИСПОЛЬЗУЮ TIMING ATTACK НА СРАВНЕНИЕ ПАРОЛЕЙ",
			"НАШЁЛ HARDCODED CREDENTIALS В DOCKER IMAGE",
			"РАЗБИРАЮ ОБФУСЦИРОВАННЫЙ JAVASCRIPT...",
			"ЛОМАЮ JWT ТОКЕН ЧЕРЕЗ NONE ALGORITHM",
			"ПОДКЛЮЧАЮСЬ К НЕЗАЩИЩЁННОМУ MONGODB БЕЗ ПАРОЛЯ",
			"НАХОЖУ ОТКРЫТЫЙ S3 BUCKET С БЭКАПАМИ",
			"ИСПОЛЬЗУЮ DIRTY COW EXPLOIT НА СТАРОМ ЯДРЕ",
			"ИНЖЕКТИРУЮ КОМАНДУ ЧЕРЕЗ PDF МЕТАДАННЫЕ",
			"ДЕЛАЮ SUBDOMAIN TAKEOVER ЧЕРЕЗ CNAME",
			"ОТКЛЮЧАЮ АНТИВИРУС ЧЕРЕЗ ГРУППОВЫЕ ПОЛИТИКИ",
			"ВНЕДРЯЮСЬ В СЕТЬ ЧЕРЕЗ ПРИНТЕР HP",
			"КРЕПЛЮ БЭКДОР К ОБНОВЛЕНИЮ WINDOWS",
			"ИСПОЛЬЗУЮ ETERNAL BLUE... КЛАССИКА!",
			"ВЗЛАМЫВАЮ РОУТЕР ЧЕРЕЗ UPnP УЯЗВИМОСТЬ",
			"МЕНЯЮ DNS НА 8.8.8.8... ПОДОЖДИТЕ, ЭТО ГУГЛ",
			"СКАЧИВАЮ ПАРОЛИ ИЗ CHROME ЧЕРЕЗ SQLITE",
			"ПЕРЕХВАТЫВАЮ СЕССИЮ ЧЕРЕЗ COOKIE HIJACKING",
			"ДЕЛАЮ HEAP SPRAY В БРАУЗЕРЕ",
			"ОБХОЖУ ASLR ЧЕРЕЗ INFORMATION LEAK",
			"ЭКСПЛУАТИРУЮ USE-AFTER-FREE В CHROME",
			"ВНЕДРЯЮ ВРЕДОНОСНЫЙ КОД В NPM ПАКЕТ",
			"АТАКУЮ SUPPLY CHAIN ЧЕРЕЗ PYPI",
			"ИСПОЛЬЗУЮ TYPOSQUATTING НА GITHUB",
		]

		self.fake_errors = [
			"⚠ БРАНДМАУЭР ОБНАРУЖЕН! ОБХОЖУ...",
			"⚠ АНТИВИРУС КАСПЕРСКОГО ДЕТЕКТИТ PAYLOAD!",
			"⚠ ОБНАРУЖЕНА IDS/IPS СИСТЕМА!",
			"⚠ WAF БЛОКИРУЕТ ЗАПРОСЫ!",
			"⚠ SELINUX БЛОКИРУЕТ ДОСТУП!",
			"⚠ RATE LIMITING АКТИВИРОВАН!",
			"⚠ IP ЗАБЛОКИРОВАН! ПЕРЕКЛЮЧАЮ ПРОКСИ...",
			"⚠ CAPTCHA ОБНАРУЖЕНА!",
			"⚠ HONEYPOT ОБНАРУЖЕН! ОБХОЖУ...",
			"⚠ FAIL2BAN ЗАБЛОКИРОВАЛ SSH!",
			"⚠ CLOUDFLARE PROTECTION АКТИВНА!",
			"⚠ ДВУХФАКТОРНАЯ АУТЕНТИФИКАЦИЯ!",
			"⚠ ОБНАРУЖЕНА СИСТЕМА МОНИТОРИНГА SPLUNK!",
			"⚠ СЕТЕВОЙ КАРАНТИН АКТИВИРОВАН!",
			"⚠ WINDOWS DEFENDER АГРЕССИВНИЧАЕТ!",
			"⚠ NORTON ANTIVIRUS ПАНИКУЕТ!",
			"⚠ MCAFEE СЪЕЛ ВСЮ ПАМЯТЬ!",
			"⚠ EDR РЕШЕНИЕ ДЕТЕКТИТ ПОВЕДЕНИЕ!",
			"⚠ SIEM СИСТЕМА АЛЕРТИТ!",
			"⚠ SOC КОМАНДА ПРОСЫПАЕТСЯ!",
			"⚠ ГЕОБЛОКИРОВКА АКТИВНА!",
			"⚠ VPN ДЕТЕКТОР СРАБОТАЛ!",
			"⚠ TOR EXIT NODE ЗАБЛОКИРОВАН!",
			"⚠ SSL PINNING МЕШАЕТ MITM!",
			"⚠ CERTIFICATE TRANSPARENCY ПАЛИТ!",
		]

		self.scan_messages = [
			"Сканирую порт {port}... {status}",
			"TCP SYN на порт {port}: {status}",
			"UDP probe порт {port}: {status}",
			"Проверка сервиса на порту {port}: {service}",
			"Banner grab порт {port}: {banner}",
			"Fingerprint OS: {os_name}",
			"Версия сервера: {server}",
			"SSL/TLS версия: {tls}",
			"Обнаружен открытый порт: {port}",
			"Проверяю CVE для сервиса на порту {port}...",
			"NSE скрипт на порту {port}...",
			"Определяю версию сервиса {port}...",
			"Проверка на default credentials {port}...",
		]

		self.data_messages = [
			"Скачиваю таблицу users... {size} записей",
			"Дамп хешей паролей: {count} найдено",
			"Экспорт emails: {count} адресов",
			"Копирую /etc/passwd...",
			"Скачиваю конфигурацию nginx...",
			"Читаю .env файл... найдены API ключи!",
			"Дамп базы данных: {db_name} ({size} MB)",
			"Скачиваю SSL сертификаты...",
			"Копирую SSH ключи из ~/.ssh/",
			"Экспорт cookies: {count} штук",
			"Скачиваю логи доступа: access.log ({size} MB)",
			"Дамп Redis: {count} ключей",
			"Копирую Docker secrets...",
			"Читаю /proc/self/environ...",
			"Скачиваю бэкап: backup_{date}.tar.gz",
			"Экспорт кредитных карт: {count} (ТЕСТОВЫХ!)",
			"Дамп MongoDB коллекции: {collection}",
			"Скачиваю приватные репозитории...",
			"Копирую .git директорию...",
			"Извлекаю secrets из Kubernetes...",
			"Дамп переменных окружения...",
			"Скачиваю приватные ключи...",
			"Копирую историю bash...",
			"Извлекаю токены из localStorage...",
			"Дамп session storage...",
			"Скачиваю конфиг базы данных...",
			"Копирую AWS credentials...",
			"Извлекаю GCP service account...",
			"Дамп Azure AD токенов...",
		]

		self.apply_theme()
		self.show_splash_screen()

	def show_splash_screen(self):
		self.splash = tk.Toplevel(self.root)
		self.splash.title("")
		self.splash.geometry("700x400")
		self.splash.configure(bg='#000000')
		self.splash.resizable(False, False)
		self.splash.overrideredirect(True)

		self.splash.update_idletasks()
		x = (self.splash.winfo_screenwidth() - 700) // 2
		y = (self.splash.winfo_screenheight() - 400) // 2
		self.splash.geometry(f"700x400+{x}+{y}")

		logo = random.choice(ASCII_LOGOS)
		tk.Label(self.splash, text=logo,
				 bg='#000000', fg=self.theme['accent'],
				 font=('Consolas', 10), justify='left').pack(pady=20)

		tk.Label(self.splash, text="SECURITY EXPLOIT KIT v5.0.0",
				 bg='#000000', fg=self.theme['fg_main'],
				 font=('Consolas', 16, 'bold')).pack()

		tk.Label(self.splash, text="Загрузка...",
				 bg='#000000', fg=self.theme['fg_dim'],
				 font=('Consolas', 10)).pack(pady=10)

		self.splash_progress = ttk.Progressbar(self.splash, mode='determinate', length=400)
		self.splash_progress.pack(pady=10)

		self.root.withdraw()
		self._animate_splash(0)

	def _animate_splash(self, progress):
		if progress > 100:
			self.splash.destroy()
			self.root.deiconify()
			self.create_widgets()
			self.start_background_tasks()
			self.log_welcome()
			
			# Запрос имени при первом запуске
			if not self.player_data.get('name', ''):
				self.root.after(500, self.ask_player_name)
			else:
				self.root.after(500, self.show_welcome_message)
			return

		self.splash_progress['value'] = progress
		self.splash.after(25, lambda: self._animate_splash(progress + 2))

	def apply_theme(self):
		self.root.configure(bg=self.theme['bg_dark'])

	def load_settings(self):
		"""Загрузка настроек из файла"""
		try:
			settings_file = Path.home() / ".hacker_settings.json"
			if settings_file.exists():
				with open(settings_file, 'r') as f:
					data = json.load(f)
					self.current_theme_name = data.get('theme', 'matrix')
					self.minigame_chance = data.get('minigame_chance', 20)
					self.glitch_enabled = data.get('glitch_enabled', True)
					self.show_calculations = data.get('show_calculations', True)
					self.attack_mode = data.get('attack_mode', 'normal')
				
					# Проверяем что тема существует
					if self.current_theme_name not in THEMES:
						self.current_theme_name = 'matrix'
				
					self.theme = THEMES[self.current_theme_name]
		except Exception:
			# Если ошибка — используем значения по умолчанию
			self.current_theme_name = "matrix"
			self.theme = THEMES[self.current_theme_name]
			self.minigame_chance = 20
			self.glitch_enabled = True
			self.show_calculations = True
			self.attack_mode = "normal"


	def save_settings(self):
		"""Сохранение настроек в файл"""
		try:
			settings_file = Path.home() / ".hacker_settings.json"
			data = {
				'theme': self.current_theme_name,
				'minigame_chance': self.minigame_chance,
				'glitch_enabled': self.glitch_enabled,
				'show_calculations': self.show_calculations,
				'attack_mode': self.attack_mode,
			}
			with open(settings_file, 'w') as f:
				json.dump(data, f, indent=2)
		except Exception:
			pass

	def load_player_data(self):
		"""Загрузка профиля игрока"""
		default = {
			'name': '',
			'money': 0,
			'total_earned': 0,
			'hacks_completed': 0,
			'hacks_failed': 0,
			'data_stolen_gb': 0.0,
			'skill_points': 0,
			'skills': {
				'hacking_speed': 1,
				'minigame_difficulty': 1,
				'earning_rate': 1,
				'stealth': 1,
			},
		}
		try:
			player_file = Path.home() / ".hacker_profile.json"
			if player_file.exists():
				with open(player_file, 'r', encoding='utf-8') as f:
					data = json.load(f)
					for key in default:
						if key not in data:
							data[key] = default[key]
					self.player_data = data
			else:
				self.player_data = default
		except Exception:
			self.player_data = default

	def save_player_data(self):
		"""Сохранение профиля игрока"""
		try:
			player_file = Path.home() / ".hacker_profile.json"
			with open(player_file, 'w', encoding='utf-8') as f:
				json.dump(self.player_data, f, indent=2, ensure_ascii=False)
		except Exception:
			pass

	def delete_player_data(self):
		"""Удаление профиля"""
		try:
			player_file = Path.home() / ".hacker_profile.json"
			if player_file.exists():
				player_file.unlink()
		except Exception:
			pass

	def ask_player_name(self):
		"""Запрос имени при первом запуске"""
		dialog = tk.Toplevel(self.root)
		dialog.title("👤 Добро пожаловать!")
		dialog.geometry("400x200")
		dialog.configure(bg=self.theme['bg_dark'])
		dialog.resizable(False, False)
		dialog.grab_set()

		tk.Label(dialog, text="Представься, хакер:",
				 bg=self.theme['bg_dark'], fg=self.theme['fg_main'],
				 font=('Consolas', 11)).pack(pady=20)

		name_var = tk.StringVar()
		entry = tk.Entry(dialog, textvariable=name_var,
						 bg=self.theme['bg_medium'], fg=self.theme['fg_main'],
						 font=('Consolas', 14), justify='center')
		entry.pack(pady=10, padx=50)
		entry.focus_set()

		def submit():
			name = name_var.get().strip()
			if name:
				self.player_data['name'] = name
				self.save_player_data()
				self.log_message(f"▶ Хакер '{name}' в сети", "success")
				dialog.destroy()

		entry.bind('<Return>', lambda e: submit())
		tk.Button(dialog, text="ВВОД",
				  bg=self.theme['bg_medium'], fg=self.theme['accent'],
				  font=('Consolas', 11),
				  command=submit).pack(pady=10)

	def show_welcome_message(self):
		"""Приветствие с балансом"""
		self.log_message("═" * 50, "header")
		self.log_message("  ТВОЙ ПРОФИЛЬ", "header")
		self.log_message("═" * 50, "header")
		self.log_message(f"  Баланс: ${self.player_data['money']}", "data")
		self.log_message(f"  Заработано: ${self.player_data['total_earned']}", "data")
		self.log_message(f"  Взломов: {self.player_data['hacks_completed']}", "info")
		self.log_message("═" * 50, "header")

	def _update_balance_display(self):
		"""Обновляет отображение баланса и имени"""
		try:
			self.name_label.config(text=f"👤 {self.player_data.get('name', 'Анон')}")
			self.balance_label.config(text=f"💵 ${self.player_data.get('money', 0)}")
			# Обновляем профиль в центре
			self.profile_name.config(text=f"👤 {self.player_data.get('name', 'Анон')}")
			self.profile_money.config(text=f"💵 ${self.player_data.get('money', 0)}")
			self.profile_stats.config(text=f"Взломов: {self.player_data.get('hacks_completed', 0)}")
			self.profile_sp.config(text=f"SP: {self.player_data.get('skill_points', 0)}")
		except:
			pass

	def open_skills_window(self):
		"""Окно прокачки навыков"""
		skills = tk.Toplevel(self.root)
		skills.title("⚡ НАВЫКИ")
		skills.geometry("450x450")
		skills.configure(bg=self.theme['bg_dark'])
		skills.resizable(False, False)
		skills.grab_set()

		tk.Label(skills, text="⚡ НАВЫКИ ХАКЕРА",
				 bg=self.theme['bg_dark'], fg=self.theme['fg_main'],
				 font=('Consolas', 14, 'bold')).pack(pady=15)

		tk.Label(skills, text=f"Доступно SP: {self.player_data['skill_points']}",
				 bg=self.theme['bg_dark'], fg=self.theme['accent'],
				 font=('Consolas', 12, 'bold')).pack(pady=10)

		skill_defs = {
			'hacking_speed': ('🚀 Скорость взлома', 'Ускоряет симуляцию', 1.0),
			'minigame_difficulty': ('🎮 Лёгкость мини-игр', 'Проще мини-игры', 1.0),
			'earning_rate': ('💰 Доход', 'Больше денег', 1.5),
			'stealth': ('👻 Скрытность', 'Дольше не палят', 1.2),
		}

		for skill_id, (name, desc, cost_mult) in skill_defs.items():
			level = self.player_data['skills'][skill_id]
			cost = int(100 * cost_mult * level)
			
			frame = tk.Frame(skills, bg=self.theme['bg_medium'])
			frame.pack(fill=tk.X, padx=20, pady=5)
			
			left = tk.Frame(frame, bg=self.theme['bg_medium'])
			left.pack(side=tk.LEFT, fill=tk.X, expand=True)
			
			tk.Label(left, text=name,
					 bg=self.theme['bg_medium'], fg=self.theme['fg_main'],
					 font=('Consolas', 10, 'bold')).pack(anchor='w')
			tk.Label(left, text=desc,
					 bg=self.theme['bg_medium'], fg=self.theme['fg_dim'],
					 font=('Consolas', 8)).pack(anchor='w')
			
			bar = '█' * level + '░' * (10 - level)
			tk.Label(left, text=f"[{bar}] Lvl {level}",
					 bg=self.theme['bg_medium'], fg=self.theme['accent'],
					 font=('Consolas', 8)).pack(anchor='w')
			
			right = tk.Frame(frame, bg=self.theme['bg_medium'])
			right.pack(side=tk.RIGHT, padx=10)
			
			if level < 10:
				tk.Label(right, text=f"${cost}",
						 bg=self.theme['bg_medium'], fg=self.theme['warning'],
						 font=('Consolas', 9)).pack()
				
				def upgrade(sid=skill_id, c=cost, cm=cost_mult):
					if self.player_data['skill_points'] >= 1 and self.player_data['money'] >= c:
						self.player_data['skill_points'] -= 1
						self.player_data['money'] -= c
						self.player_data['skills'][sid] += 1
						self.save_player_data()
						self._update_balance_display()
						skills.destroy()
						self.open_skills_window()
					else:
						if self.player_data['skill_points'] < 1:
							messagebox.showwarning("Нет SP", "Нужен 1 SP!")
						if self.player_data['money'] < c:
							messagebox.showwarning("Нет денег", f"Нужно ${c}!")
				
				tk.Button(right, text="▲",
						  bg=self.theme['bg_dark'], fg=self.theme['fg_main'],
						  font=('Consolas', 10, 'bold'),
						  command=upgrade).pack()
			else:
				tk.Label(right, text="MAX",
						 bg=self.theme['bg_medium'], fg='#00ff00',
						 font=('Consolas', 9, 'bold')).pack()

		tk.Label(skills, text="\nНавыки за SP и $",
				 bg=self.theme['bg_dark'], fg=self.theme['fg_dim'],
				 font=('Consolas', 8)).pack()

	def create_widgets(self):
		main = tk.Frame(self.root, bg=self.theme['bg_dark'])
		main.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

		# === Верхняя панель ===
		top = tk.Frame(main, bg=self.theme['bg_dark'])
		top.pack(fill=tk.X, pady=(0, 6))

		tk.Label(top, text="◆ SECURITY EXPLOIT KIT v5.0.0",
				 bg=self.theme['bg_dark'], fg=self.theme['fg_main'],
				 font=('Consolas', 14, 'bold')).pack(side=tk.LEFT, padx=10)

		# Индикаторы
		ind_frame = tk.Frame(top, bg=self.theme['bg_dark'])
		ind_frame.pack(side=tk.LEFT, padx=20)

		self.status_labels = []
		for name in ["DARKNET", "TOR", "VPN", "CRYPTO"]:
			frame = tk.Frame(ind_frame, bg=self.theme['bg_medium'],
							 highlightbackground=self.theme['border'],
							 highlightthickness=1, padx=6, pady=2)
			frame.pack(side=tk.LEFT, padx=2)

			tk.Label(frame, text=name, bg=self.theme['bg_medium'],
					 fg=self.theme['fg_dim'], font=('Consolas', 7)).pack()

			status = tk.Label(frame, text="●", bg=self.theme['bg_medium'],
							  fg=self.theme['fg_main'], font=('Consolas', 10, 'bold'))
			status.pack()
			self.status_labels.append(status)

		# Режим атаки
		mode_frame = tk.Frame(top, bg=self.theme['bg_dark'])
		mode_frame.pack(side=tk.LEFT, padx=20)

		tk.Label(mode_frame, text="Режим:",
				 bg=self.theme['bg_dark'], fg=self.theme['fg_dim'],
				 font=('Consolas', 9)).pack(side=tk.LEFT)

		self.mode_var = tk.StringVar(value=self.attack_mode)
		modes = [("🐢 Стелс", "stealth"), ("⚡ Норм", "normal"), ("🔥 Агрессив", "aggressive")]
		for text, mode in modes:
			rb = tk.Radiobutton(mode_frame, text=text, variable=self.mode_var, value=mode,
								bg=self.theme['bg_dark'], fg=self.theme['fg_main'],
								selectcolor=self.theme['bg_medium'],
								activebackground=self.theme['bg_dark'],
								font=('Consolas', 9),
								command=self._update_mode)
			rb.pack(side=tk.LEFT, padx=3)

		# Кнопки справа
		btn_frame = tk.Frame(top, bg=self.theme['bg_dark'])
		btn_frame.pack(side=tk.RIGHT, padx=10)

		# Баланс и имя
		balance_frame = tk.Frame(top, bg=self.theme['bg_medium'],
								  highlightbackground=self.theme['border'],
								  highlightthickness=1, padx=15, pady=3)
		balance_frame.pack(side=tk.RIGHT, padx=10)

		self.balance_label = tk.Label(balance_frame,
									  text=f"💵 ${self.player_data.get('money', 0)}",
									  bg=self.theme['bg_medium'],
									  fg=self.theme['accent'],
									  font=('Consolas', 10, 'bold'))
		self.balance_label.pack(side=tk.RIGHT, padx=(15, 0))

		self.name_label = tk.Label(balance_frame,
								   text=f"👤 {self.player_data.get('name', 'Анон')}",
								   bg=self.theme['bg_medium'],
								   fg=self.theme['fg_main'],
								   font=('Consolas', 9))
		self.name_label.pack(side=tk.RIGHT)

		tk.Button(btn_frame, text="🖥 Консоль",
				  bg=self.theme['bg_medium'], fg=self.theme['fg_main'],
				  font=('Consolas', 9),
				  command=self.open_console).pack(side=tk.LEFT, padx=3)

		tk.Button(btn_frame, text="⚙",
				  bg=self.theme['bg_medium'], fg=self.theme['fg_main'],
				  font=('Consolas', 9),
				  command=self.open_settings).pack(side=tk.LEFT, padx=3)

		tk.Button(btn_frame, text="📜",
				  bg=self.theme['bg_medium'], fg=self.theme['fg_main'],
				  font=('Consolas', 9),
				  command=self.open_history).pack(side=tk.LEFT, padx=3)

		tk.Button(btn_frame, text="⏻",
				  bg='#1a0d0d', fg='#ff4444',
				  font=('Consolas', 9),
				  command=self.on_close).pack(side=tk.LEFT, padx=3)

		tk.Frame(main, bg=self.theme['border'], height=1).pack(fill=tk.X, pady=3)

		# === Средняя часть ===
		middle = tk.Frame(main, bg=self.theme['bg_dark'])
		middle.pack(fill=tk.BOTH, expand=True, pady=(6, 6))

		# --- Левая панель ---
		left = tk.Frame(middle, bg=self.theme['bg_dark'], width=320)
		left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 6))
		left.pack_propagate(False)

		tk.Label(left, text="◆ ЦЕЛИ",
				 bg=self.theme['bg_dark'], fg=self.theme['fg_main'],
				 font=('Consolas', 11, 'bold')).pack(anchor='w', pady=(0, 5))

		list_cont = tk.Frame(left, bg=self.theme['border'])
		list_cont.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

		scrollbar = tk.Scrollbar(list_cont)
		scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

		self.target_listbox = tk.Listbox(list_cont,
										 bg=self.theme['bg_dark'],
										 fg=self.theme['fg_main'],
										 font=('Consolas', 10),
										 selectbackground=self.theme['bg_light'],
										 selectforeground=self.theme['accent'],
										 selectmode=tk.EXTENDED,
										 activestyle='none',
										 yscrollcommand=scrollbar.set)
		self.target_listbox.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
		scrollbar.config(command=self.target_listbox.yview)

		for t in self.target_list:
			self.target_listbox.insert(tk.END, t)

		self.selected_var = tk.StringVar(value="Выбрано: 0")
		tk.Label(left, textvariable=self.selected_var,
				 bg=self.theme['bg_dark'], fg=self.theme['fg_dim'],
				 font=('Consolas', 9)).pack(anchor='w', pady=(0, 5))

		self.target_listbox.bind('<<ListboxSelect>>', self._on_selection)

		# Кастомная цель
		tk.Label(left, text="Добавить:",
				 bg=self.theme['bg_dark'], fg=self.theme['fg_dim'],
				 font=('Consolas', 9)).pack(anchor='w')

		custom_frame = tk.Frame(left, bg=self.theme['bg_dark'])
		custom_frame.pack(fill=tk.X, pady=(0, 8))

		self.custom_var = tk.StringVar()
		tk.Entry(custom_frame, textvariable=self.custom_var,
				 bg=self.theme['bg_medium'], fg=self.theme['fg_main'],
				 insertbackground=self.theme['accent'],
				 font=('Consolas', 10), width=20).pack(side=tk.LEFT, padx=(0, 5))

		tk.Button(custom_frame, text="+",
				  bg=self.theme['bg_medium'], fg=self.theme['accent'],
				  font=('Consolas', 10, 'bold'),
				  command=self.add_custom_target).pack(side=tk.LEFT)

		# Кнопки
		tk.Button(left, text="Выбрать все",
				  bg=self.theme['bg_medium'], fg=self.theme['fg_main'],
				  font=('Consolas', 10),
				  command=self.select_all).pack(fill=tk.X, pady=2)

		tk.Button(left, text="Снять выбор",
				  bg=self.theme['bg_medium'], fg=self.theme['fg_main'],
				  font=('Consolas', 10),
				  command=self.deselect_all).pack(fill=tk.X, pady=2)

		tk.Frame(left, bg=self.theme['bg_dark'], height=10).pack()

		tk.Button(left, text="◆ ВЗЛОМАТЬ ◆",
				  bg='#1a0d0d', fg='#ff3333',
				  font=('Consolas', 12, 'bold'),
				  command=self.start_hacking).pack(fill=tk.X, pady=2)

		tk.Button(left, text="⚠ Замести следы",
				  bg='#1a0d0d', fg='#ff6666',
				  font=('Consolas', 10),
				  command=self.emergency_exit).pack(fill=tk.X, pady=2)

		# --- Центр ---
		center = tk.Frame(middle, bg=self.theme['bg_dark'], width=280)
		center.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 6))
		center.pack_propagate(False)

		# Матрица
		tk.Label(center, text="◆ DATA STREAM",
				 bg=self.theme['bg_dark'], fg=self.theme['fg_main'],
				 font=('Consolas', 11, 'bold')).pack(anchor='w', pady=(0, 5))

		matrix_cont = tk.Frame(center, bg=self.theme['border'])
		matrix_cont.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

		self.matrix_text = tk.Text(matrix_cont,
								   bg='#020502', fg=self.theme['matrix_fg'],
								   font=('Consolas', 8), width=30,
								   borderwidth=0, highlightthickness=0)
		self.matrix_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

		# Профиль игрока
		tk.Label(center, text="◆ ПРОФИЛЬ",
				 bg=self.theme['bg_dark'], fg=self.theme['fg_main'],
				 font=('Consolas', 11, 'bold')).pack(anchor='w', pady=(10, 5))

		profile_frame = tk.Frame(center, bg=self.theme['border'])
		profile_frame.pack(fill=tk.X, pady=(0, 6))

		# Имя
		self.profile_name = tk.Label(profile_frame,
									 text=f"👤 {self.player_data.get('name', 'Анон')}",
									 bg=self.theme['bg_dark'],
									 fg=self.theme['fg_main'],
									 font=('Consolas', 10, 'bold'),
									 anchor='w')
		self.profile_name.pack(fill=tk.X, padx=5, pady=3)

		# Баланс
		self.profile_money = tk.Label(profile_frame,
									  text=f"💵 ${self.player_data.get('money', 0)}",
									  bg=self.theme['bg_dark'],
									  fg=self.theme['accent'],
									  font=('Consolas', 10, 'bold'),
									  anchor='w')
		self.profile_money.pack(fill=tk.X, padx=5, pady=3)

		# Статистика
		self.profile_stats = tk.Label(profile_frame,
									  text=f"Взломов: {self.player_data.get('hacks_completed', 0)}",
									  bg=self.theme['bg_dark'],
									  fg=self.theme['fg_dim'],
									  font=('Consolas', 9),
									  anchor='w')
		self.profile_stats.pack(fill=tk.X, padx=5, pady=3)

		self.profile_sp = tk.Label(profile_frame,
								   text=f"SP: {self.player_data.get('skill_points', 0)}",
								   bg=self.theme['bg_dark'],
								   fg='#ffcc00',
								   font=('Consolas', 9),
								   anchor='w')
		self.profile_sp.pack(fill=tk.X, padx=5, pady=3)

		# Кнопка навыков
		tk.Button(center, text="⚡ НАВЫКИ",
				  bg=self.theme['bg_medium'], fg=self.theme['accent'],
				  font=('Consolas', 10, 'bold'),
				  command=self.open_skills_window).pack(fill=tk.X, pady=5)

		# --- Правая панель (логи) ---
		log_frame = tk.Frame(middle, bg=self.theme['bg_dark'])
		log_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

		tk.Label(log_frame, text="◆ EXPLOIT LOG",
				 bg=self.theme['bg_dark'], fg=self.theme['fg_main'],
				 font=('Consolas', 11, 'bold')).pack(anchor='w', pady=(0, 5))

		log_cont = tk.Frame(log_frame, bg=self.theme['border'])
		log_cont.pack(fill=tk.BOTH, expand=True)

		self.log_text = scrolledtext.ScrolledText(log_cont,
												  bg=self.theme['bg_dark'],
												  fg=self.theme['fg_main'],
												  font=('Consolas', 10),
												  borderwidth=0,
												  highlightthickness=0,
												  wrap=tk.WORD)
		self.log_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

		# Теги
		self.log_text.tag_config("timestamp", foreground="#555555")
		self.log_text.tag_config("info", foreground=self.theme['fg_main'])
		self.log_text.tag_config("success", foreground=self.theme['accent'])
		self.log_text.tag_config("warning", foreground=self.theme['warning'])
		self.log_text.tag_config("error", foreground=self.theme['error'])
		self.log_text.tag_config("header", foreground='#00cccc')
		self.log_text.tag_config("stupid", foreground='#cc66ff')
		self.log_text.tag_config("data", foreground=self.theme['data'])
		self.log_text.tag_config("fast", foreground=self.theme['fg_dim'])
		self.log_text.tag_config("calc", foreground='#666666')
		self.log_text.tag_config("minigame", foreground='#ff8800')

		tk.Button(log_frame, text="💾 Экспорт",
				  bg=self.theme['bg_medium'], fg=self.theme['fg_main'],
				  font=('Consolas', 9),
				  command=self.export_logs).pack(anchor='e', pady=(5, 0))

		# === Нижняя панель ===
		tk.Frame(main, bg=self.theme['border'], height=1).pack(fill=tk.X, pady=3)

		bottom = tk.Frame(main, bg=self.theme['bg_dark'])
		bottom.pack(fill=tk.X, pady=(6, 0))

		prog_label = tk.Frame(bottom, bg=self.theme['bg_dark'])
		prog_label.pack(fill=tk.X)

		tk.Label(prog_label, text="PROGRESS",
				 bg=self.theme['bg_dark'], fg=self.theme['fg_dim'],
				 font=('Consolas', 9)).pack(side=tk.LEFT)

		self.progress_percent = tk.Label(prog_label, text="IDLE",
										 bg=self.theme['bg_dark'], fg=self.theme['fg_main'],
										 font=('Consolas', 9, 'bold'))
		self.progress_percent.pack(side=tk.RIGHT)

		self.progress_var = tk.DoubleVar(value=100.0)
		style = ttk.Style()
		style.configure("Custom.Horizontal.TProgressbar",
						background=self.theme['accent'],
						troughcolor=self.theme['bg_medium'])

		self.progress_bar = ttk.Progressbar(bottom, mode='determinate',
											variable=self.progress_var,
											style="Custom.Horizontal.TProgressbar")
		self.progress_bar.pack(fill=tk.X, pady=(4, 4))

		self.status_var = tk.StringVar(value="СТАТУС: Ожидание...")
		tk.Label(bottom, textvariable=self.status_var,
				 bg=self.theme['bg_dark'], fg=self.theme['fg_main'],
				 font=('Consolas', 10)).pack(anchor='w')

		# Обновляем баланс
		self._update_balance_display()

	def _update_mode(self):
		"""Обновляет режим атаки"""
		self.attack_mode = self.mode_var.get()

	def _on_selection(self, event=None):
		"""Обработка клика по цели — добавляет порядок атаки"""
		selection = self.target_listbox.curselection()
		
		if selection:
			last_selected = selection[-1]
			target = self.target_listbox.get(last_selected)
			
			# Проверяем есть ли уже номер порядка
			has_order = target.startswith('[') and ']' in target
			
			if has_order:
				# Уже в порядке — снимаем выделение и убираем номер
				parts = target.split('] ', 1)
				if len(parts) > 1:
					original_name = parts[1]
					self.target_listbox.delete(last_selected)
					self.target_listbox.insert(last_selected, original_name)
					
					# Удаляем из порядка
					if original_name in self.target_order:
						del self.target_order[original_name]
					
					# Пересчитываем номера
					self._renumber_targets()
			else:
				# Нет номера — добавляем
				if target not in self.target_order:
					self.click_count += 1
					self.target_order[target] = self.click_count
					self.target_listbox.delete(last_selected)
					self.target_listbox.insert(last_selected, f"[{self.click_count}] {target}")
		
		# Выделяем все цели с номерами
		self._highlight_ordered_targets()
		
		count = len(self.target_order)
		self.selected_var.set(f"В очереди: {self.click_count}")

	def _highlight_ordered_targets(self):
		"""Выделяет все цели с номерами порядка"""
		self.target_listbox.selection_clear(0, tk.END)
		for i in range(self.target_listbox.size()):
			item = self.target_listbox.get(i)
			if item.startswith('[') and ']' in item:
				self.target_listbox.selection_set(i)

	def _renumber_targets(self):
		"""Пересчитывает номера целей после удаления"""
		items = []
		for i in range(self.target_listbox.size()):
			item = self.target_listbox.get(i)
			if item.startswith('[') and ']' in item:
				parts = item.split('] ', 1)
				if len(parts) > 1:
					items.append((i, parts[1]))
		
		items.sort(key=lambda x: self.target_order.get(x[1], 999))
		
		self.click_count = 0
		for idx, (i, name) in enumerate(items):
			self.click_count += 1
			self.target_order[name] = self.click_count
			self.target_listbox.delete(i)
			self.target_listbox.insert(i, f"[{self.click_count}] {name}")
		
		# Выделяем все цели с номерами
		self._highlight_ordered_targets()

	def select_all(self):
		"""Выбрать все — сбрасывает порядок"""
		self.target_order.clear()
		self.click_count = 0
		self._refresh_target_list()
		self.target_listbox.select_set(0, tk.END)
		self._on_selection()

	def deselect_all(self):
		"""Снять все — сбрасывает порядок"""
		self.target_order.clear()
		self.click_count = 0
		self._refresh_target_list()
		self.target_listbox.selection_clear(0, tk.END)
		self.selected_var.set("В очереди: 0")

	def _refresh_target_list(self):
		"""Перерисовывает список целей без номеров порядка"""
		current = self.target_listbox.get(0, tk.END)
		self.target_listbox.delete(0, tk.END)
		for item in current:
			if item.startswith('[') and ']' in item:
				parts = item.split('] ', 1)
				if len(parts) > 1:
					item = parts[1]
			self.target_listbox.insert(tk.END, item)
		
		# Сбрасываем выделение
		self.target_listbox.selection_clear(0, tk.END)

	def add_custom_target(self):
		target = self.custom_var.get().strip()
		if target:
			if "/" not in target:
				target = f"{target} / {target}"
			self.target_list.append(target)
			self.target_listbox.insert(tk.END, target)
			self.custom_var.set("")
			self.log_message(f"  + Добавлено: {target}", "success")

	def safe_call(self, func, *args):
		try:
			self.root.after(0, func, *args)
		except:
			pass

	def log_message(self, message, msg_type="info"):
		timestamp = datetime.now().strftime("%H:%M:%S")
		if message == "":
			self.log_text.insert(tk.END, "\n")
		else:
			self.log_text.insert(tk.END, f" {timestamp} │ ", "timestamp")
			self.log_text.insert(tk.END, f"{message}\n", msg_type)
		self.log_text.see(tk.END)

	def log_welcome(self):
		self.log_message("═" * 50, "header")
		self.log_message("  SECURITY EXPLOIT KIT v5.0.0", "header")
		self.log_message("═" * 50, "header")
		self.log_message("")
		self.log_message("  Все модули загружены", "success")
		self.log_message("  Режимы: 🐢Стелс | ⚡Норм | 🔥Агрессив", "info")
		self.log_message("  📊 = График | 🖥 = Консоль отладки", "info")
		self.log_message("")

	def _do_log(self, msg, msg_type):
		try:
			self.log_message(msg, msg_type)
		except:
			pass

	def _do_status(self, text):
		try:
			self.status_var.set(text)
		except:
			pass

	def _do_progress(self, val, text=None):
		try:
			self.progress_var.set(val)
			if text:
				self.progress_percent.config(text=text)
		except:
			pass

	def _do_matrix(self, line):
		try:
			self.matrix_text.insert(1.0, line + "\n")
			count = int(self.matrix_text.index('end-1c').split('.')[0])
			if count > 80:
				self.matrix_text.delete(f"{count - 1}.0", tk.END)
		except:
			pass

	def _generate_calc(self):
		"""Случайный расчёт"""
		a = random.randint(1, 1000)
		b = random.randint(-100, 500)
		ops = [('+', a + b), ('-', a - b), ('×', a * b)]
		if b != 0:
			ops.append(('÷', round(a / b, 2)))
		op, result = random.choice(ops)
		return f"    [{a} {op} {b} = {result}]"

	def _generate_hex(self):
		return ''.join(random.choice('0123456789abcdef') for _ in range(32))

	def _generate_scan(self):
		"""Генерирует сообщение сканирования"""
		port = random.choice([21, 22, 23, 25, 53, 80, 110, 143, 443, 445,
							  993, 995, 1433, 1521, 3306, 3389, 5432,
							  5900, 6379, 8080, 8443, 9200, 27017])
		status = random.choice(["OPEN", "OPEN", "OPEN", "CLOSED", "FILTERED"])
		service = random.choice(["HTTP", "SSH", "FTP", "SMTP", "DNS",
								  "MySQL", "PostgreSQL", "Redis", "MongoDB",
								  "RDP", "nginx", "Apache", "IIS", "Node.js"])
    
		templates = [
			f"Порт {port}: {status}",
			f"TCP {port} → {status} ({service})",
			f"Сканирую {port}... {status}",
			f"{service} на порту {port}: {status}",
			f"Banner {port}: {service}/1.0",
		]
		return random.choice(templates)

	def _generate_data(self):
		"""Генерирует сообщение извлечения данных"""
		templates = [
			f"Таблица users: {random.randint(100, 999999)} записей",
			f"Хеши паролей: {random.randint(50, 50000)} MD5/SHA256",
			f"Email адреса: {random.randint(100, 100000)} штук",
			f"Копирую /etc/shadow...",
			f"Читаю .env... API_KEY найден!",
			f"База данных: {random.randint(10, 500)} MB",
			f"SSH ключи: {random.randint(1, 20)} найдено",
			f"Cookies: {random.randint(50, 5000)} сессий",
			f"Логи: access.log ({random.randint(100, 999)} MB)",
			f"Redis dump: {random.randint(1000, 99999)} ключей",
			f"Docker secrets: {random.randint(5, 50)} найдено",
			f"AWS credentials... JACKPOT!",
			f"Приватный ключ RSA 4096... есть!",
			f"Git history: {random.randint(100, 5000)} коммитов",
			f"Кредитки: {random.randint(100, 9999)} (тестовые!)",
			f"Фотки котиков: {random.randint(1, 100)} 🐱",
			f"Секретные документы: {random.randint(10, 500)} PDF",
			f"Пароли в plaintext: {random.randint(50, 5000)} 🤦",
		]
		return random.choice(templates)

	# ═══════════════════════════════════════════════════════════════════════════
	# МИНИ-ИГРЫ
	# ═══════════════════════════════════════════════════════════════════════════

	def _trigger_minigame(self, target_name):
		"""Запускает мини-игру"""
		self.minigame_result = None
		self.minigame_event.clear()

		def on_win():
			self.minigame_result = True
			self.minigame_event.set()

		def on_lose():
			self.minigame_result = False
			self.minigame_event.set()

		games = [
			("Камень-Ножницы-Бумага", RockPaperScissorsGame),
			("Крестики-Нолики", TicTacToeGame),
			("Последовательность", SimonSaysGame),
			("Бомба", WireDefuseGame),
			("Печать кода", TypeCodeGame),
			("Лабиринт", MazeGame),
			("Сейф", SafeCrackGame),
			("Математика", MathGame),
		]

		name, game_class = random.choice(games)

		self.safe_call(self._do_log, "", "info")
		self.safe_call(self._do_log, f"  ⚠ ЗАЩИТА: {name}!", "minigame")
		self.safe_call(self._do_log, f"  ⚠ Требуется обход!", "minigame")

		time.sleep(0.5)

		def launch():
			game_class(self.root, target_name, on_win, on_lose, self.theme)

		self.safe_call(launch)
		self.minigame_event.wait()

		return self.minigame_result

	# ═══════════════════════════════════════════════════════════════════════════
	# ФОНОВЫЕ ПРОЦЕССЫ
	# ═══════════════════════════════════════════════════════════════════════════

	def update_matrix(self):
		chars = "qwertyuiopasdfghjklzxcvbnmйцукенгшщзхфывапролджэячсмитьбю123456789"
		while self.matrix_running:
			if random.random() < 0.15:
				line = ''.join(random.choice(chars) for _ in range(random.randint(15, 30)))
				self.safe_call(self._do_matrix, line)
			time.sleep(0.04)

	def update_indicators(self):
		while self.matrix_running:
			for label in self.status_labels:
				color = random.choice([self.theme['fg_main'], self.theme['accent'],
									   self.theme['warning'], '#cc44cc'])
				self.safe_call(lambda l=label, c=color: l.config(fg=c))
			time.sleep(random.uniform(2, 4))

	def update_glitch(self):
		while self.matrix_running:
			if self.glitch_enabled and random.random() < 0.03:
				def glitch():
					try:
						orig = self.log_text.cget('bg')
						colors = ['#100000', '#001000', '#000010']
						self.log_text.config(bg=random.choice(colors))
						self.root.after(50, lambda: self.log_text.config(bg=orig))
					except:
						pass
				self.safe_call(glitch)
			time.sleep(0.5)

	def start_background_tasks(self):
		for func in [self.update_matrix, self.update_indicators,
					 self.update_glitch]:
			threading.Thread(target=func, daemon=True).start()

	# ═══════════════════════════════════════════════════════════════════════════
	# СИМУЛЯЦИЯ ВЗЛОМА
	# ═══════════════════════════════════════════════════════════════════════════

	def _get_mode_params(self):
		"""Параметры в зависимости от режима"""
		if self.attack_mode == "stealth":
			return {
				'delay_mult': 2.0,
				'minigame_mult': 0.3,
				'log_detail': 'low',
			}
		elif self.attack_mode == "aggressive":
			return {
				'delay_mult': 0.3,
				'minigame_mult': 2.0,
				'log_detail': 'high',
			}
		else:  # normal
			return {
				'delay_mult': 1.0,
				'minigame_mult': 1.0,
				'log_detail': 'medium',
			}

	def hacking_simulation(self):
		self.is_hacking = True
		params = self._get_mode_params()

		# Получаем цели в порядке кликов
		selection = self.target_listbox.curselection()
		if selection:
			# Сортируем по порядку кликов
			ordered_targets = []
			for i in selection:
				target = self.target_listbox.get(i)
				# Удаляем префикс [N] если есть
				if target.startswith('[') and ']' in target:
					parts = target.split('] ', 1)
					if len(parts) > 1:
						target = parts[1]
				order = self.target_order.get(target, 999)
				ordered_targets.append((order, target))
			
			# Сортируем по порядку клика
			ordered_targets.sort(key=lambda x: x[0])
			targets = [t[1] for t in ordered_targets]
		else:
			targets = [random.choice(self.target_list)]
			self.safe_call(self._do_log, "⚠ Цель не выбрана, атакую случайную", "warning")

		total = len(targets)
		completed = 0
		failed = 0

		self.safe_call(self._do_log, "", "info")
		self.safe_call(self._do_log, "═" * 50, "header")
		self.safe_call(self._do_log, f"  АТАКА НА {total} ЦЕЛЬ(ЕЙ) [{self.attack_mode.upper()}]", "header")
		self.safe_call(self._do_log, "═" * 50, "header")

		self.safe_call(self._do_progress, 0, "0%")

		for idx, target in enumerate(targets):
			if not self.is_hacking:
				break

			target_name = target.split(" / ")[0].upper()
			base_progress = (idx / total) * 100
			skipped = False

			# Пасхалка
			if "127.0.0.1" in target or "localhost" in target:
				self.safe_call(self._do_log, "", "info")
				self.safe_call(self._do_log, "  🤔 Ты взламываешь сам себя!", "warning")
				self.safe_call(self._do_log, "  🤔 Это... интересная стратегия", "warning")
				time.sleep(1 * params['delay_mult'])

			self.safe_call(self._do_log, "", "info")
			self.safe_call(self._do_log, "─" * 40, "info")
			self.safe_call(self._do_log, f"  ◆ [{idx+1}/{total}] {target}", "header")
			self.safe_call(self._do_log, "─" * 40, "info")
			self.safe_call(self._do_status, f"Атакую {target_name}")

			# Мигаем на карте
			self.safe_call(lambda: self._flash_attack_point(
				random.randint(20, 240), random.randint(15, 100)))

			# === ФАЗА 1: Разведка ===
			self.safe_call(self._do_log, "", "info")
			self.safe_call(self._do_log, f"  [1/5] Разведка", "warning")

			ip = f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
			self.safe_call(self._do_log, f"  DNS: {target_name} → {ip}", "info")
			time.sleep(0.3 * params['delay_mult'])

			if self.show_calculations:
				for _ in range(random.randint(2, 4)):
					self.safe_call(self._do_log, self._generate_calc(), "calc")
					time.sleep(0.02 * params['delay_mult'])

			self.safe_call(self._do_log, f"  Traceroute: {random.randint(8, 20)} hops", "info")
			time.sleep(0.2 * params['delay_mult'])

			phase_progress = base_progress + (10 / total)
			self.safe_call(self._do_progress, phase_progress, f"{int(phase_progress)}%")

			# === ФАЗА 2: Сканирование ===
			if not self.is_hacking:
				break

			self.safe_call(self._do_log, "", "info")
			self.safe_call(self._do_log, f"  [2/5] Сканирование", "warning")

			scan_count = 10 if params['log_detail'] == 'low' else 20 if params['log_detail'] == 'medium' else 35
			for _ in range(scan_count):
				if not self.is_hacking:
					break
				self.safe_call(self._do_log, f"    {self._generate_scan()}", "fast")
				if self.show_calculations and random.random() < 0.2:
					self.safe_call(self._do_log, self._generate_calc(), "calc")
				time.sleep(random.uniform(0.01, 0.06) * params['delay_mult'])

			self.safe_call(self._do_log, f"  ✓ Найдено {random.randint(3, 10)} портов", "success")

			phase_progress = base_progress + (25 / total)
			self.safe_call(self._do_progress, phase_progress, f"{int(phase_progress)}%")

			# ★ МИНИ-ИГРА ★
			effective_chance = self.minigame_chance * params['minigame_mult']
			if not self.is_hacking:
				break

			if random.randint(1, 100) <= effective_chance:
				won = self._trigger_minigame(target_name)
				if won:
					self.safe_call(self._do_log, f"  ✓ Защита обойдена!", "success")
				else:
					self.safe_call(self._do_log, f"  ✗ Провал! Пропускаю...", "error")
					failed += 1
					skipped = True
				time.sleep(0.3)

			if skipped or not self.is_hacking:
				phase_progress = base_progress + (100 / total)
				self.safe_call(self._do_progress, phase_progress, f"{int(min(phase_progress, 99))}%")
				continue

			# === ФАЗА 3: Эксплуатация ===
			self.safe_call(self._do_log, "", "info")
			self.safe_call(self._do_log, f"  [3/5] Эксплуатация", "warning")

			exploit_count = 4 if params['log_detail'] == 'low' else 7 if params['log_detail'] == 'medium' else 12
			for _ in range(exploit_count):
				if not self.is_hacking:
					break

				self.safe_call(self._do_log, f"    {random.choice(self.stupid_messages)}", "stupid")
				time.sleep(random.uniform(0.2, 0.5) * params['delay_mult'])

				if self.show_calculations:
					for _ in range(random.randint(1, 3)):
						self.safe_call(self._do_log, self._generate_calc(), "calc")
						time.sleep(0.01)

				if random.random() < 0.2:
					self.safe_call(self._do_log, f"    {random.choice(self.fake_errors)}", "error")
					time.sleep(0.2 * params['delay_mult'])
					self.safe_call(self._do_log, f"    ✓ Обход!", "success")

				# Hex спам в aggressive режиме
				if params['log_detail'] == 'high' and random.random() < 0.4:
					for _ in range(random.randint(5, 10)):
						self.safe_call(self._do_log, f"      0x{self._generate_hex()}", "fast")
						time.sleep(0.005)

			phase_progress = base_progress + (55 / total)
			self.safe_call(self._do_progress, phase_progress, f"{int(phase_progress)}%")

			# === ФАЗА 4: Доступ ===
			if not self.is_hacking:
				break

			self.safe_call(self._do_log, "", "info")
			self.safe_call(self._do_log, f"  [4/5] Получение доступа", "warning")

			access_msgs = [
				f"Shell → {ip}:4444",
				"Привилегии: root",
				"Файловая система: ДА",
				"База данных: ДА",
			]
			for msg in access_msgs:
				if not self.is_hacking:
					break
				self.safe_call(self._do_log, f"    ✓ {msg}", "success")
				time.sleep(0.2 * params['delay_mult'])

			phase_progress = base_progress + (75 / total)
			self.safe_call(self._do_progress, phase_progress, f"{int(phase_progress)}%")

			# === ФАЗА 5: Извлечение ===
			if not self.is_hacking:
				break

			self.safe_call(self._do_log, "", "info")
			self.safe_call(self._do_log, f"  [5/5] Извлечение данных", "warning")

			data_count = 5 if params['log_detail'] == 'low' else 10 if params['log_detail'] == 'medium' else 18
			for _ in range(data_count):
				if not self.is_hacking:
					break
				self.safe_call(self._do_log, f"    ↓ {self._generate_data()}", "data")
				if self.show_calculations and random.random() < 0.3:
					self.safe_call(self._do_log, self._generate_calc(), "calc")
				time.sleep(random.uniform(0.01, 0.1) * params['delay_mult'])

			if self.is_hacking:
				self.safe_call(self._do_log, "", "info")
				self.safe_call(self._do_log, f"  ✓ {target_name} ВЗЛОМАН!", "success")
				self.safe_call(self._do_log, f"  ✓ Данные: {random.uniform(0.5, 50):.1f} GB", "success")
				completed += 1

			phase_progress = base_progress + (100 / total)
			self.safe_call(self._do_progress, phase_progress, f"{int(min(phase_progress, 99))}%")
			time.sleep(0.3 * params['delay_mult'])

		# === Финал ===
		if self.is_hacking:
			self.safe_call(self._do_progress, 100, "100%")
			time.sleep(0.3)

			self.safe_call(self._do_log, "", "info")
			self.safe_call(self._do_log, "═" * 50, "header")
			self.safe_call(self._do_log, f"  ЗАВЕРШЕНО!", "header")
			self.safe_call(self._do_log, f"  Успешно: {completed}/{total}", "success")
			if failed > 0:
				self.safe_call(self._do_log, f"  Провалено: {failed}/{total}", "error")
			self.safe_call(self._do_log, "═" * 50, "header")

			if completed > 0:
				# Начисление денег и опыта
				base_reward = random.randint(50, 200) * completed
				earning_skill = self.player_data['skills']['earning_rate']
				multiplier = 1 + (earning_skill - 1) * 0.15
				total_reward = int(base_reward * multiplier)
				
				self.player_data['money'] += total_reward
				self.player_data['total_earned'] += total_reward
				self.player_data['hacks_completed'] += completed
				self.player_data['data_stolen_gb'] += random.uniform(0.5, 50) * completed
				self.player_data['skill_points'] += completed
				self.save_player_data()
				
				# Обновляем баланс в UI
				self.safe_call(self._update_balance_display)
				
				self.safe_call(self._do_log, "", "info")
				self.safe_call(self._do_log, "═" * 50, "header")
				self.safe_call(self._do_log, f"  ЗАРАБОТАНО: ${total_reward}", "success")
				self.safe_call(self._do_log, f"  ОПЫТ: +{completed} SP", "data")
				self.safe_call(self._do_log, f"  БАЛАНС: ${self.player_data['money']}", "success")
				self.safe_call(self._do_log, "═" * 50, "header")
				
				self.safe_call(self._do_log, "", "info")
				self.safe_call(self._do_log, "  Украдено:", "success")
				self.safe_call(self._do_log, f"    • Паролей: {random.randint(1000, 999999)}", "data")
				self.safe_call(self._do_log, f"    • Email: {random.randint(5000, 999999)}", "data")
				self.safe_call(self._do_log, f"    • Котиков: {random.randint(1, 42)} 🐱", "data")

			self.safe_call(self._do_status, f"Взломано {completed}, провалено {failed}")

			self.attack_history.append({
				"date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
				"targets": total,
				"completed": completed,
				"failed": failed,
				"mode": self.attack_mode,
			})
			self.save_history()

			time.sleep(1)
			self.safe_call(self._do_progress, 100, "IDLE")
		else:
			self.safe_call(self._do_log, "", "info")
			self.safe_call(self._do_log, "⚠ ПРЕРВАНО!", "error")
			self.safe_call(self._do_status, "Прервано")
			self.safe_call(self._do_progress, 100, "IDLE")

		self.is_hacking = False

	def start_hacking(self):
		if not self.is_hacking:
			threading.Thread(target=self.hacking_simulation, daemon=True).start()
		else:
			self.log_message("⚠ Уже выполняется!", "warning")

	def emergency_exit(self):
		self.is_hacking = False
		self.minigame_event.set()
		self.log_text.delete(1.0, tk.END)
		self.progress_var.set(100)
		self.progress_percent.config(text="IDLE")
		
		# Сброс порядка целей
		self.target_order.clear()
		self.click_count = 0
		self._refresh_target_list()

		self.log_message("", "info")
		self.log_message("⚠ ════════════════════════════════════ ⚠", "error")
		self.log_message("  EMERGENCY EXIT", "error")
		self.log_message("⚠ ════════════════════════════════════ ⚠", "error")
		self.log_message("")
		for step in ["Логи", "Кэш", "TOR", "MAC", "Прокси"]:
			self.log_message(f"  {step}... OK", "warning")
		self.log_message("")
		self.log_message("  Система очищена", "success")
		self.status_var.set("Следы заметены")

	# ═══════════════════════════════════════════════════════════════════════════
	# КОНСОЛЬ ОТЛАДКИ
	# ═══════════════════════════════════════════════════════════════════════════

	def open_console(self):
		"""Консоль отладки"""
		console = tk.Toplevel(self.root)
		console.title("🖥 Debug Console")
		console.geometry("600x500")
		console.configure(bg='#0a0a0a')

		tk.Label(console, text="🖥 DEBUG CONSOLE",
				 bg='#0a0a0a', fg='#00ff00',
				 font=('Consolas', 14, 'bold')).pack(pady=10)

		tk.Label(console, text="Команды: help, minigame <name>, theme <name>, mode <name>, clear",
				 bg='#0a0a0a', fg='#888888',
				 font=('Consolas', 9)).pack()

		# Вывод
		output_frame = tk.Frame(console, bg='#1a1a1a')
		output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

		self.console_output = scrolledtext.ScrolledText(output_frame,
														bg='#000000', fg='#00ff00',
														font=('Consolas', 10),
														height=15)
		self.console_output.pack(fill=tk.BOTH, expand=True)

		# Ввод
		input_frame = tk.Frame(console, bg='#0a0a0a')
		input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

		tk.Label(input_frame, text=">",
				 bg='#0a0a0a', fg='#00ff00',
				 font=('Consolas', 12, 'bold')).pack(side=tk.LEFT)

		self.console_input = tk.Entry(input_frame,
									  bg='#000000', fg='#00ff00',
									  insertbackground='#00ff00',
									  font=('Consolas', 12))
		self.console_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
		self.console_input.focus_set()
		self.console_input.bind('<Return>', lambda e: self._exec_console_cmd())

		tk.Button(input_frame, text="Run",
				  bg='#003300', fg='#00ff00',
				  font=('Consolas', 10),
				  command=self._exec_console_cmd).pack(side=tk.RIGHT)

		# Быстрые кнопки для мини-игр
		tk.Label(console, text="Мини-игры:",
				 bg='#0a0a0a', fg='#888888',
				 font=('Consolas', 9)).pack()

		games_frame = tk.Frame(console, bg='#0a0a0a')
		games_frame.pack(pady=5)

		games = ["rps", "tictactoe", "simon", "wire", "type", "maze", "safe", "math"]
		for game in games:
			tk.Button(games_frame, text=game,
					  bg='#1a1a1a', fg='#00cc00',
					  font=('Consolas', 8),
					  command=lambda g=game: self._run_minigame_debug(g)).pack(side=tk.LEFT, padx=2)

		self._console_print("Debug Console v1.0")
		self._console_print("Введите 'help' для списка команд")
		self._console_print("")

	def _console_print(self, text):
		self.console_output.insert(tk.END, text + "\n")
		self.console_output.see(tk.END)

	def _exec_console_cmd(self):
		cmd = self.console_input.get().strip().lower()
		self.console_input.delete(0, tk.END)

		if not cmd:
			return

		self._console_print(f"> {cmd}")

		parts = cmd.split()
		command = parts[0]
		args = parts[1:] if len(parts) > 1 else []

		if command == "help":
			self._console_print("Команды:")
			self._console_print("  help              - Эта справка")
			self._console_print("  minigame <name>   - Запустить мини-игру")
			self._console_print("    Игры: rps, tictactoe, simon, wire, type, maze, safe, math")
			self._console_print("  theme <name>      - Сменить тему")
			self._console_print("    Темы: matrix, cyberpunk, blood, ocean, amber")
			self._console_print("  mode <name>       - Режим атаки")
			self._console_print("    Режимы: stealth, normal, aggressive")
			self._console_print("  chance <0-100>    - Шанс мини-игры")
			self._console_print("  clear             - Очистить консоль")
			self._console_print("  status            - Статус системы")

		elif command == "minigame" and args:
			self._run_minigame_debug(args[0])

		elif command == "theme" and args:
			if args[0] in THEMES:
				self.current_theme_name = args[0]
				self.theme = THEMES[args[0]]
				self._console_print(f"Тема: {args[0]} (перезапустите для полного эффекта)")
			else:
				self._console_print(f"Неизвестная тема: {args[0]}")

		elif command == "mode" and args:
			if args[0] in ["stealth", "normal", "aggressive"]:
				self.attack_mode = args[0]
				self.mode_var.set(args[0])
				self._console_print(f"Режим: {args[0]}")
			else:
				self._console_print(f"Неизвестный режим: {args[0]}")

		elif command == "chance" and args:
			try:
				val = int(args[0])
				self.minigame_chance = max(10, min(100, val))
				self._console_print(f"Шанс мини-игры: {self.minigame_chance}%")
			except:
				self._console_print("Ошибка: введите число 10-100")

		elif command == "clear":
			self.console_output.delete(1.0, tk.END)

		elif command == "status":
			self._console_print(f"Тема: {self.current_theme_name}")
			self._console_print(f"Режим: {self.attack_mode}")
			self._console_print(f"Шанс мини-игры: {self.minigame_chance}%")
			self._console_print(f"Глитчи: {self.glitch_enabled}")
			self._console_print(f"Расчёты: {self.show_calculations}")
			self._console_print(f"Хакинг активен: {self.is_hacking}")

		else:
			self._console_print(f"Неизвестная команда: {command}")

		self._console_print("")

	def _run_minigame_debug(self, game_name):
		"""Запуск мини-игры из консоли"""
		games_map = {
			"rps": RockPaperScissorsGame,
			"tictactoe": TicTacToeGame,
			"simon": SimonSaysGame,
			"wire": WireDefuseGame,
			"type": TypeCodeGame,
			"maze": MazeGame,
			"safe": SafeCrackGame,
			"math": MathGame,
		}

		if game_name in games_map:
			def on_result(win):
				self._console_print(f"Результат: {'ПОБЕДА!' if win else 'ПРОИГРЫШ'}")

			games_map[game_name](self.root, "DEBUG", 
								 lambda: on_result(True), 
								 lambda: on_result(False), 
								 self.theme)
			self._console_print(f"Запущено: {game_name}")
		else:
			self._console_print(f"Неизвестная игра: {game_name}")

	# ═══════════════════════════════════════════════════════════════════════════
	# НАСТРОЙКИ И ИСТОРИЯ
	# ═══════════════════════════════════════════════════════════════════════════

	def open_settings(self):
		settings = tk.Toplevel(self.root)
		settings.title("⚙ Настройки")
		settings.geometry("450x550")
		settings.configure(bg=self.theme['bg_dark'])
		settings.resizable(False, False)
		settings.grab_set()

		tk.Label(settings, text="⚙ НАСТРОЙКИ",
				 bg=self.theme['bg_dark'], fg=self.theme['fg_main'],
				 font=('Consolas', 14, 'bold')).pack(pady=(15, 20))

		# Тема
		tk.Label(settings, text="Тема:",
				 bg=self.theme['bg_dark'], fg=self.theme['fg_main'],
				 font=('Consolas', 10)).pack(anchor='w', padx=20)

		self.settings_theme_var = tk.StringVar(value=self.current_theme_name)
		for tid, tdata in THEMES.items():
			tk.Radiobutton(settings, text=tdata['name'],
						   variable=self.settings_theme_var, value=tid,
						   bg=self.theme['bg_dark'], fg=self.theme['fg_main'],
						   selectcolor=self.theme['bg_medium'],
						   activebackground=self.theme['bg_dark'],
						   font=('Consolas', 10)).pack(anchor='w', padx=40)

		# Шанс мини-игры (10-100)
		tk.Label(settings, text="Шанс мини-игры (10-100%):",
				 bg=self.theme['bg_dark'], fg=self.theme['fg_main'],
				 font=('Consolas', 10)).pack(anchor='w', padx=20, pady=(15, 0))

		self.settings_chance_var = tk.IntVar(value=self.minigame_chance)
		tk.Scale(settings, from_=10, to=100, orient=tk.HORIZONTAL,
				 variable=self.settings_chance_var,
				 bg=self.theme['bg_dark'], fg=self.theme['fg_main'],
				 highlightthickness=0, length=300).pack(padx=40)

		# Чекбоксы
		self.settings_glitch_var = tk.BooleanVar(value=self.glitch_enabled)
		tk.Checkbutton(settings, text="Глитч-эффекты",
					   variable=self.settings_glitch_var,
					   bg=self.theme['bg_dark'], fg=self.theme['fg_main'],
					   selectcolor=self.theme['bg_medium'],
					   font=('Consolas', 10)).pack(anchor='w', padx=20, pady=(10, 0))

		self.settings_calc_var = tk.BooleanVar(value=self.show_calculations)
		tk.Checkbutton(settings, text="Показывать расчёты",
					   variable=self.settings_calc_var,
					   bg=self.theme['bg_dark'], fg=self.theme['fg_main'],
					   selectcolor=self.theme['bg_medium'],
					   font=('Consolas', 10)).pack(anchor='w', padx=20)

		def save():
			self.current_theme_name = self.settings_theme_var.get()
			self.theme = THEMES[self.current_theme_name]
			self.minigame_chance = self.settings_chance_var.get()
			self.glitch_enabled = self.settings_glitch_var.get()
			self.show_calculations = self.settings_calc_var.get()
		
			# СОХРАНЯЕМ В ФАЙЛ!
			self.save_settings()
		
			messagebox.showinfo("OK", "Сохранено!\nТема полностью применится при перезапуске.")
			settings.destroy()

		tk.Button(settings, text="💾 Сохранить",
				  bg=self.theme['bg_medium'], fg=self.theme['fg_main'],
				  font=('Consolas', 12, 'bold'),
				  command=save).pack(pady=20)

	def load_history(self):
		try:
			path = Path.home() / ".hacker_history.json"
			if path.exists():
				with open(path, 'r') as f:
					self.attack_history = json.load(f)
		except:
			self.attack_history = []

	def save_history(self):
		try:
			path = Path.home() / ".hacker_history.json"
			with open(path, 'w') as f:
				json.dump(self.attack_history[-100:], f)
		except:
			pass

	def open_history(self):
		history = tk.Toplevel(self.root)
		history.title("📜 История")
		history.geometry("550x400")
		history.configure(bg=self.theme['bg_dark'])

		tk.Label(history, text="📜 ИСТОРИЯ АТАК",
				 bg=self.theme['bg_dark'], fg=self.theme['fg_main'],
				 font=('Consolas', 14, 'bold')).pack(pady=10)

		cols = ("Дата", "Целей", "Успех", "Провал", "Режим")
		tree = ttk.Treeview(history, columns=cols, show='headings', height=12)

		for col in cols:
			tree.heading(col, text=col)
			tree.column(col, width=100, anchor='center')

		for e in reversed(self.attack_history[-50:]):
			tree.insert('', 'end', values=(
				e.get('date', ''),
				e.get('targets', 0),
				e.get('completed', 0),
				e.get('failed', 0),
				e.get('mode', 'normal'),
			))

		tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

		if self.attack_history:
			total = len(self.attack_history)
			success = sum(e.get('completed', 0) for e in self.attack_history)
			tk.Label(history, text=f"Всего атак: {total} | Успешных целей: {success}",
					 bg=self.theme['bg_dark'], fg=self.theme['fg_dim'],
					 font=('Consolas', 10)).pack(pady=5)

	def export_logs(self):
		path = filedialog.asksaveasfilename(
			defaultextension=".txt",
			filetypes=[("Text", "*.txt")],
			initialfile=f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
		)
		if path:
			try:
				with open(path, 'w', encoding='utf-8') as f:
					f.write(self.log_text.get(1.0, tk.END))
				messagebox.showinfo("OK", f"Сохранено: {path}")
			except Exception as e:
				messagebox.showerror("Ошибка", str(e))

	def on_close(self):
		self.matrix_running = False
		self.is_hacking = False
		self.minigame_event.set()
		self.save_history()
		self.save_settings()
		self.save_player_data()  # Сохраняем профиль
		self.root.quit()
		self.root.destroy()


# ═══════════════════════════════════════════════════════════════════════════════
# ЗАПУСК
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
	root = tk.Tk()
	app = HackersTerminal(root)
	root.mainloop()