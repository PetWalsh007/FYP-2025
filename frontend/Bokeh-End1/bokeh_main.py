# Dev main file for Bokeh front end 

from bokeh.plotting import figure, curdoc, show
from bokeh.models import HoverTool
from bokeh.layouts import column


# test a simple plot

# create a plot and style its properties
p = figure(x_axis_label='x', y_axis_label='y')
p.line(x=[1, 2, 3], y=[4, 6, 5], line_width=2)

# add a hover tool to the plot
hover = HoverTool()
hover.tooltips = [('x', '@x'), ('y', '@y')]

p.add_tools(hover)

# create a layout for the plot
layout = column(p)

# add the layout to curdoc
curdoc().add_root(layout)

show(layout)
