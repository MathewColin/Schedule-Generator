from orar import State
import numpy as np
import random
from copy import deepcopy

import utils

def stochastic_hill_climbing(initial: State, max_iters: int = 400):
	iters, states = 0, 0
	state = initial

	# se seteaza un numar maximum de iteratii
	while iters < max_iters:
		iters += 1

		my_actions = state.get_neighbours()
		succesors_acc = []

		# se cauta in vecinii starii curente
		for s in my_actions:
			states += 1

			# conditia impusa e ca numarul de conflicte sa nu creasca fata de starea precedenta
			if state.conflicts_count() >= state.conflicts_count(action=s):
				succesors_acc.append(s)

		# daca nu mai exista actiuni posbile, ne oprim, starea nu e finala
		if len(my_actions) == 0:
			break

		# daca nu exista succesori care sa respecte conditia, se aleg din cei care aduc numar minimum de conflicte
		if len(succesors_acc) == 0:
			mini = random.choice(list(my_actions))
			for s in my_actions:
				if mini is None:
					mini = s
					continue

				if state.conflicts_count(mini) > state.conflicts_count(action=s):
					mini = s
			for s in my_actions:
				if state.conflicts_count(action=s) == state.conflicts_count(action=mini):
					succesors_acc.append(s)

		prob = [1/(1 + state.conflicts_count(x)) for x in succesors_acc]
		prob = [x / sum(prob) for x in prob]
		acc = succesors_acc[np.random.choice(len(succesors_acc), p=prob)]
		state = state.apply_action(acc)
	return state.is_final(), iters, states, state

def random_restart_hill_climbing(
		initial,
		teachers,
		subjects,
		days,
		intervals,
		rooms,
		intervals_teachers,
		teacher_to_subject,
		subject_to_room,
		teacher_to_not_days,
		teacher_to_not_intervals,
		teacher_to_pause,
		max_restarts = 300,
		run_max_iters = 400,
):

	is_final = False
	total_iters, total_states = 0, 0

	st = initial
	restarts = 0

	# cautam solutia exacta, daca nu exista, o cautam pe cea cu numar minimum de conflicte incalcate
	sol = None

	while restarts < max_restarts:
		print('Restart: ' + str(restarts))
		final, current_iter, curr_state, st = stochastic_hill_climbing(st, run_max_iters)

		print('Result: ' + str(final) + ' ' + str(st.conflicts_count()))

		total_iters += current_iter
		total_states += curr_state

		# daca s-a gasit o solutie exacta, algoritmul se opreste
		if final and st.conflicts_count() == 0:
			is_final = True
			break

		# daca s-a gasit o solutie finala, dar nu exacta, aceasta se compara cu solutia precedenta
		# iar algoritmul isi continua cautarea
		if final:
			is_final = True
			if sol is None:
				sol = deepcopy(st)

			if sol is not None:
				if sol.conflicts_count() > st.conflicts_count():
					sol = deepcopy(st)

		st = State(teachers, subjects, days, intervals, rooms, {}, intervals_teachers,
				   teacher_to_subject, subject_to_room, teacher_to_not_days, teacher_to_not_intervals,
				   teacher_to_pause, start=True)
		restarts += 1

	# se alege solutia exacta sau doar finala care urmeaza a fi afisata
	if st.conflicts_count() == 0 and st.is_final() and is_final:
		state = st
	else:
		state = sol

	if is_final == False:
		is_final = state.is_final()

	return is_final, total_iters, total_states, state
