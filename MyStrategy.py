from random import randrange
from model.ActionType import ActionType
from model.TrooperType import TrooperType
from model.CellType import CellType

WIDTH = 30
HEIGHT = 20

D = 1

cells = []


class CellList(list):
    def __contains__(self, item):
        for element in self:
            if element.x == item.x and element.y == item.y:
                return True

        return False


def is_walkable_cell(x, y):
    global cells

    return cells[x][y] == CellType.FREE


def heuristic_cost(point_a, point_b):
        dx1 = abs(point_a.x - point_b.x)
        dy1 = abs(point_a.y - point_b.y)
        #dx2 = (start.x - end.x)
        #dy2 = (start.y - end.y)
        #cross = abs(dx1*dy2 - dx2*dy1)
        #
        #return cross*0.001

        return D*(dx1 + dy1)


def a_star(start, end):
    closed_set = CellList()
    open_set = CellList()
    open_set.append(start)

    start.g = 0
    start.f = start.g + heuristic_cost(start, end)

    while open_set:
        current = min(open_set)
        if current.x == end.x and current.y == end.y:
            if None == end.parent:
                end.parent = current

            return reconstruct_path(end)

        open_set.remove(current)
        closed_set.append(current)

        for neighbor in current.neighbors():
            tentative_g = current.g + D
            tentative_f = tentative_g + heuristic_cost(neighbor, end)

            if neighbor in closed_set and tentative_f >= neighbor.f:
                continue

            if neighbor not in open_set or tentative_f < neighbor.f:
                neighbor.parent = current
                neighbor.g = tentative_g
                neighbor.f = tentative_f

                if neighbor not in open_set:
                    open_set.append(neighbor)

    raise ValueError('Could not find a path')


def reconstruct_path(end):
    path = []
    current = end.parent
    while current:
        path.append(current)
        current = current.parent

    return path


class Cell:
    x = 0
    y = 0
    g = 0.0
    h = 0.0
    f = 0.0
    parent = None

    def __init__(self, x, y):
        self.x, self.y = x, y

    def __repr__(self):
        return '[%d, %d] g = %d, h = %.2f, f = %.2f'%(self.x, self.y, self.g, self.h, self.f) + "\n"

    def __cmp__(self, other):
        return self.f - other.f

    def neighbors(self):
        neighbors = []
        if self.x > 0 and is_walkable_cell(self.x - 1, self.y):
            neighbors.append(Cell(self.x - 1, self.y))  # left

        if self.x < WIDTH - 1 and is_walkable_cell(self.x + 1, self.y):
            neighbors.append(Cell(self.x + 1, self.y))  # right

        if self.y > 0 and is_walkable_cell(self.x, self.y - 1):
            neighbors.append(Cell(self.x, self.y - 1))  # up

        if self.y < HEIGHT - 1 and is_walkable_cell(self.x, self.y + 1):
            neighbors.append(Cell(self.x, self.y + 1))  # down

        return neighbors

com_path = []
med_path = []
sol_path = []

last_tick = -1
target = None


class MyStrategy:
    def move(self, me, world, game, move):
        global cells, com_path, med_path, sol_path, last_tick, target
        cells = world.cells

        if last_tick < 0:
            last_tick = world.move_index

        if me.action_points < game.standing_move_cost:
            return

        if me.type == TrooperType.COMMANDER and not com_path:
            x, y = self.random_visible_cell(me, cells)
            print [x, y], cells[x][y]
            com_path = a_star(Cell(me.x, me.y), Cell(x, y))
            #print "Commander path: \n", com_path, "\n"
        elif me.type == TrooperType.FIELD_MEDIC and not med_path:
            x, y = self.random_visible_cell(me, cells)
            print [x, y], cells[x][y]
            med_path = a_star(Cell(me.x, me.y), Cell(x, y))
            #print "Med path: ", med_path, "\n"
        elif me.type == TrooperType.SOLDIER and not sol_path:
            x, y = self.random_visible_cell(me, cells)
            print [x, y], cells[x][y]
            sol_path = a_star(Cell(me.x, me.y), Cell(x, y))
            #print "Sol path: ", sol_path, "\n"

        enemy = None
        for trooper in world.troopers:
            if not trooper.teammate:
                if not enemy:
                    enemy = trooper
                else:
                    if me.get_distance_to_unit(trooper) < me.get_distance_to_unit(enemy):
                        enemy = trooper

        if enemy:
            if me.get_distance_to_unit(enemy) < me.shooting_range and me.action_points >= me.shoot_cost:
                move.action = ActionType.SHOOT
                move.x, move.y = enemy.x, enemy.y

                last_tick = world.move_index
                #t_type = self.get_type_name(me.type)
                #print '%s (%d, %d) shooting to enemy on (%d, %d)'%(t_type, me.x, me.y, enemy.x, enemy.y)

                return

        if me.type == TrooperType.COMMANDER:
            wp = com_path.pop()
            move.action = ActionType.MOVE
            move.x, move.y = wp.x, wp.y
        elif me.type == TrooperType.SOLDIER:
            wp = sol_path.pop()
            move.action = ActionType.MOVE
            move.x, move.y = wp.x, wp.y
        elif me.type == TrooperType.FIELD_MEDIC:
            wp = med_path.pop()
            move.action = ActionType.MOVE
            move.x, move.y = wp.x, wp.y

        #t_type = self.get_type_name(me.type)
        #print '%s (%d, %d) moving to (%d, %d)'%(t_type, me.x, me.y, wp.x, wp.y)

        last_tick = world.move_index

    def get_type_name(self, t_type):
        if t_type == TrooperType.COMMANDER:
            return 'Commander'
        if t_type == TrooperType.FIELD_MEDIC:
            return 'Medic'
        if t_type == TrooperType.SOLDIER:
            return 'Soldier'

    def random_visible_cell(self, me, cells):
        x = randrange(0, WIDTH)
        y = randrange(0, HEIGHT)
        cell = cells[x][y]
        while True:
            if cell == CellType.FREE and me.x != x and me.y != y:
                return [x, y]
            x = randrange(0, WIDTH)
            y = randrange(0, HEIGHT)
            cell = cells[x][y]
