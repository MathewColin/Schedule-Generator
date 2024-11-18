# Pentru a putea fi rulat, se executa:
# python3 orar.py <input_path> <algorithm> algorithm - astar sau hc

import utils
import check_constraints

import sys
from copy import deepcopy

import time

# Reprezentarea starii:
# {zile : {interval (int, int) : {sala : (profesor, materie)}}}


class State:
	def __init__(self, teachers, subjects, days, intervals, rooms, timetable, intervals_teachers,
				 teacher_to_subject, subject_to_room, teacher_to_not_days, teacher_to_not_intervals,
				 teacher_to_pause, teacher_day_intervals={}, conflicts=0, start=False) -> None:
		self.teachers = teachers
		self.subjects = subjects
		self.days = days
		self.intervals = intervals
		self.rooms = rooms
		self.timetable = timetable
		self.intervals_teachers = intervals_teachers
		self.teacher_to_subject = teacher_to_subject
		self.subject_to_room = subject_to_room
		self.teacher_to_not_days = teacher_to_not_days
		self.teacher_to_not_intervals = teacher_to_not_intervals
		self.teacher_to_pause = teacher_to_pause
		self.conflicts = conflicts
		self.teacher_day_intervals = teacher_day_intervals

		if len(self.teacher_day_intervals) == 0:
			for teacher in self.teachers:
				self.teacher_day_intervals[teacher] = {}
				for day in days:
					self.teacher_day_intervals[teacher][day] = []

		if len(self.timetable.keys()) == 0 and start:
			for day in days:
				self.timetable[day] = {}
				for interval in intervals:
					self.timetable[day][eval(interval)] = {}
					for room in rooms:
						self.timetable[day][eval(interval)][room] = None

	def __lt__(self, other):
		return self.conflicts_count() < other.conflicts_count()

	def __eq__(self, other):
		return self.conflicts_count() == other.conflicts_count()

	def is_final(self):
		return all(self.subjects[key] == 0 for key in self.subjects.keys())

	def students_unsigned(self):
		return sum(self.subjects[key] for key in self.subjects.keys())

	def conflicts_count(self, action=None):
		if action is None:
			return self.conflicts

		cnt = self.conflicts

		if action[0] in self.teacher_to_not_days[action[2]]:
			cnt += 1

		if eval(action[1]) in self.teacher_to_not_intervals[action[2]]:
			cnt += 1

		if len(self.teacher_to_pause) != 0 and action[2] in self.teacher_to_pause:
			day = action[0]
			interval = eval(action[1])
			teacher = action[2]
			difference = self.teacher_to_pause[teacher]

			intervals_teachers = self.teacher_day_intervals[teacher][day]
			if len(intervals_teachers) == 0:
				return cnt

			pos = 0
			for i, inter in enumerate(intervals_teachers):
				if inter[0] < interval[0]:
					continue
				else:
					pos = i
					break

			if pos == 0:
				if intervals_teachers[pos][0] - interval[1] > difference:
					cnt += 1
				return cnt

			if pos == len(intervals_teachers) - 1:
				if interval[0] - intervals_teachers[pos][1] > difference:
					cnt += 1
				return cnt

			# needs to be inserted on pos, so compare with pos and pos - 1
			if intervals_teachers[pos][0] - interval[1] > difference:
				cnt += 1

			if interval[0] - intervals_teachers[pos - 1][1] > difference:
				cnt += 1


		return cnt


	def apply_action(self, action):
		self.conflicts = self.conflicts_count(action)
		(day, interval, teacher, subject, room) = action
		new_timetable = deepcopy(self.timetable)
		new_timetable[day][eval(interval)][room] = (teacher, subject)
		new_subjects = deepcopy(self.subjects)
		new_subjects[subject] -= min(self.rooms[room][utils.CAPACITATE], new_subjects[subject])
		new_intervals_teachers = deepcopy(self.intervals_teachers)
		new_intervals_teachers[teacher].add((day, interval))

		new_teacher_day_interval = deepcopy(self.teacher_day_intervals)
		new_teacher_day_interval[teacher][day].append(eval(interval))
		new_teacher_day_interval[teacher][day].sort()


		return State(self.teachers, new_subjects, self.days, self.intervals, self.rooms,
					 new_timetable, new_intervals_teachers, self.teacher_to_subject, self.subject_to_room,
					 self.teacher_to_not_days, self.teacher_to_not_intervals,
					 self.teacher_to_pause, teacher_day_intervals= new_teacher_day_interval,conflicts=self.conflicts)


	def get_neighbours(self):
		neighbours_actions = set()

		for day in self.days:
			for interval in self.intervals:
				for teacher in self.teachers:
					if (day, interval) in self.intervals_teachers[teacher] or len(
							self.intervals_teachers[teacher]) >= 7:
						continue

					for subject in self.teacher_to_subject[teacher]:
						if self.subjects[subject] == 0:
							continue

						for room in self.subject_to_room[subject]:
							# slotul este luat
							if self.timetable[day][eval(interval)][room] is not None:
								continue

							neighbours_actions.add((day, interval, teacher, subject, room))

		return neighbours_actions

def main():
	if len(sys.argv) != 3:
		print('Usage: orar.py <input_path> <HC/A*>')
		sys.exit(1)

	# Citirea datelor din yaml
	input_path = str(sys.argv[1])
	file = utils.read_yaml_file(input_path)

	# Initializarea datelor pentru clasa State
	intervals = file[utils.INTERVALE]
	teachers = file[utils.PROFESORI]
	subjects = file[utils.MATERII]
	days = file[utils.ZILE]
	rooms = file[utils.SALI]
	intervals_teachers = {}
	teacher_to_subject = {}
	subject_to_room = {}
	teacher_to_not_intervals = {}
	teacher_to_not_days = {}
	teacher_to_pause = {}

	# Extragerea constrangerilot
	for teacher in teachers:
		teacher_to_subject[teacher] = set(x for x in teachers[teacher][utils.MATERII])
		intervals_teachers[teacher] = set()
		teacher_to_not_intervals[teacher] = set()
		teacher_to_not_days[teacher] = set()
		for constraints in teachers[teacher][utils.CONSTRANGERI]:
			if '!' in constraints:
				if 'Pauza' in constraints:
					pauza_cnt = constraints.split('> ')
					pauza_cnt = int(pauza_cnt[1])
					teacher_to_pause[teacher] = pauza_cnt
					continue

				if '-' in constraints:
					# interval
					interval = constraints[1:].split('-')
					left = int(interval[0])
					right = int(interval[1])

					for x in range(left, right, 2):
						teacher_to_not_intervals[teacher].add((x, x + 2))

				else:
					# day
					day = constraints[1:]
					teacher_to_not_days[teacher].add(day)

	for room in rooms:
		for subj in rooms[room][utils.MATERII]:
			if subj not in subject_to_room.keys():
				subject_to_room[subj] = set()
			subject_to_room[subj].add(room)

	start = time.time()

	# Initializarea starii initiale
	current_state = State(teachers, subjects, days, intervals, rooms, {}, intervals_teachers,
						  teacher_to_subject, subject_to_room, teacher_to_not_days, teacher_to_not_intervals,
						  teacher_to_pause, start=True)

	algorithm = str(sys.argv[2])

	if algorithm == 'hc':

		from hill_climbing import random_restart_hill_climbing

		# Apply searching algorithms
		is_final, total_iters, total_states, state = random_restart_hill_climbing(current_state, teachers, subjects, days, intervals,
												  rooms, intervals_teachers, teacher_to_subject, subject_to_room,
												  teacher_to_not_days, teacher_to_not_intervals, teacher_to_pause)

		stop = time.time()

		print('Time taken for hill climbing: {}'.format(stop - start))

		file_name_with_extension = input_path.split("/")[-1]

		file_name = file_name_with_extension.replace(".yaml", "")

		output_path = './my_output/' + algorithm + '/' + file_name
		with open(output_path, "w") as f:
			f.write(utils.pretty_print_timetable(state.timetable, input_path))
			f.write('Mandatory Constraints: ' + str(check_constraints.check_mandatory_constraints(state.timetable, file)) + '\n')
			f.write('Optional Constraints: ' + str(check_constraints.check_optional_constraints(state.timetable, file)) + '\n')
		print(utils.pretty_print_timetable(state.timetable, input_path))
		print('Mandatory Constraints: ' + str(check_constraints.check_mandatory_constraints(state.timetable, file)))
		print('Optional Constraints: ' + str(check_constraints.check_optional_constraints(state.timetable, file)))

	elif algorithm == 'astar':
		from astar import astar
		coeficient = current_state.students_unsigned()
		h = lambda x, p: x.conflicts_count(action=p) * coeficient + x.students_unsigned()
		state, explored = astar(current_state, h)

		stop = time.time()
		print('Time taken for astar: {}'.format(stop - start))

		file_name_with_extension = input_path.split("/")[-1]

		file_name = file_name_with_extension.replace(".yaml", "")

		output_path = './my_output/' + algorithm[0] + '/' + file_name
		with open(output_path, "w") as f:
			f.write(str(explored) + '\n')
			f.write(utils.pretty_print_timetable(state.timetable, input_path))
			f.write('Mandatory Constraints: ' + str(check_constraints.check_mandatory_constraints(state.timetable, file)) + '\n')
			f.write('Optional Constraints: ' + str(check_constraints.check_optional_constraints(state.timetable, file)) + '\n')

		print(utils.pretty_print_timetable(state.timetable, input_path))
		print('Mandatory Constraints: ' + str(check_constraints.check_mandatory_constraints(state.timetable, file)))
		print('Optional Constraints: ' + str(check_constraints.check_optional_constraints(state.timetable, file)))


if __name__ == '__main__':
	main()
