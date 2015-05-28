
def pad_coord_list(l, size=2):
	"""Duplicate the first and last vertex or texture coord in a list

	Pyglet merges graphics primitives that share state, and recommends inserting
	degenerate triangles to avoid having to restart.

	See http://www.pyglet.org/doc/api/pyglet.graphics-module.html for details.
	"""
	
	return l[:size] + l + l[-size:]
