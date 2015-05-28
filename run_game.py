#!/usr/bin/python

"""The Bamboo Warrior

A PyWeek 10 game by Daniel Pope"""

from optparse import OptionParser

parser = OptionParser()
parser.add_option('-f', '--fullscreen', action='store_true', help='Start fullscreen', default=False)
parser.add_option('-d', '--resolution', help='Screen or window resolution (WxH)', default='1280x720')
parser.add_option('-p', '--profiler', action='store_true', help='Run with profiler; print stats on exit', default=False)
parser.add_option('-r', '--showfps', action='store_true', help='Show framerate display', default=False)
parser.add_option('-l', '--level', action='store', help='Start a named level')
parser.add_option('-n', '--novbo', action='store_true', help='Disable the use of VBOs (buggy/slow on some drivers)', default=False)

options, arguments = parser.parse_args()

if options.novbo:
	# monkey-patch pyglet
	from pyglet.graphics import vertexdomain
	default_create_attribute_usage = vertexdomain.create_attribute_usage
	def create_attribute_usage(format):
		attribute, usage, vbo = default_create_attribute_usage(format)
		return attribute, usage, False
	vertexdomain.create_attribute_usage = create_attribute_usage

from bamboo.game import Game

game = Game(options)

if options.level:
	from bamboo.gamestate import BambooWarriorGameState
	state = BambooWarriorGameState(game, [options.level + '.svg'])
	game.set_gamestate(state)
else:
	from bamboo.menu import MenuGameState
	state = MenuGameState(game)
	game.set_gamestate(state)

if options.profiler:
	import cProfile
	cProfile.run('game.run()', 'profiler-stats.dat')
	import pstats
	p = pstats.Stats('profiler-stats.dat')
	p.sort_stats('time').print_stats()
else:
	game.run()
