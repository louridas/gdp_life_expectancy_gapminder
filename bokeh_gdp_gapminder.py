import pandas as pd
import numpy as np
import re

import bokeh.plotting as bk

from bokeh.palettes import Spectral6
from bokeh.plotting import ColumnDataSource

from bokeh.models import (HoverTool, 
                          BoxZoomTool,
                          ResetTool,
                          PanTool,
                          WheelZoomTool,
                          Slider,
                          CustomJS,
                          Range1d,
                          Circle,
                          Text,
                          NumeralTickFormatter)

from bokeh.io import vform

gdp_df = pd.read_csv('data/gapminder/'
                     'indicator_gapminder_gdp_per_capita_ppp.csv',
                     thousands=',')

gdp_df.rename(columns={'GDP per capita': 'Entity'}, 
              inplace=True)

min_gdp = gdp_df.iloc[:,1:].min().min()
max_gdp = gdp_df.iloc[:,1:].max().max()

geographical_regions_df = pd.read_csv('data/gapminder/'
                                      'geographical_regions.csv')

all_df = pd.merge(gdp_df, 
                  geographical_regions_df[['Entity', 'Group']], 
                  on='Entity')

lex_df = pd.read_csv('data/gapminder/'
                     'indicator_gapminder_life_expectancy_at_birth.csv')

lex_df.rename(columns={'Life expectancy with projections. Yellow is IHME': 
                       'Entity'}, 
              inplace=True)


min_lex = lex_df.iloc[:,1:].min().min()
max_lex = lex_df.iloc[:,1:].max().max()

all_df = pd.merge(all_df, 
                  lex_df, 
                  on='Entity',
                  suffixes=("_gdp", "_lex"))


pop_df = pd.read_csv('data/gapminder/'
                     'indicator_gapminder_population.csv',
                     thousands=',')

pop_df.rename(columns={'Total population': 
                       'Entity'},
             inplace=True)

all_df = pd.merge(all_df, 
                  pop_df, 
                  on='Entity')              
              
for column in all_df.columns:
    col_match = re.match(r'(\d+)(_(.+))?', column)
    if col_match:
        if col_match.lastindex > 1:
            new_name = col_match.group(3) + '_' + col_match.group(1)
            all_df.rename(columns={column: new_name},
                          inplace=True)
        else:
            new_name = 'pop_' + col_match.group(1)
            all_df.rename(columns={column: new_name},
                          inplace=True)
            sizes = 0.003 * np.sqrt(all_df[new_name] / np.pi)        
            all_df['size_' + col_match.group(1)] = sizes

   

groups = geographical_regions_df['Group'].drop_duplicates()
group_map = {v: k for k, v in enumerate(groups)}
all_df['Group Code'] = all_df['Group'].map(group_map)

all_df['x'] = all_df['gdp_2015']
all_df['y'] = all_df['lex_2015']
all_df['pop'] = all_df['pop_2015']

all_df['size'] = all_df['size_2015']

colors = all_df['Group Code'].map(lambda x: Spectral6[x])

source = ColumnDataSource(all_df)

hover = HoverTool(tooltips=[
        ("Country Name", "@Entity"),
        ("Population", "@pop")
        ]
    )

min_x = 100 * (min_gdp // 100)
max_x = 1000 * (max_gdp // 1000) + 1000

min_y = 10 * (min_lex // 10)
max_y = 100 * (max_lex // 100) + 100

tools = [
    hover,
    WheelZoomTool(),
    PanTool(),
    BoxZoomTool(),
    ResetTool(),
]

p = bk.Figure(tools=tools,
              x_axis_type="log",
              x_axis_label="Income per person "
              "(GDP/capita, PPP$ inflation-adjusted)",
              y_axis_label="Life expectancy (years)",
              x_range=Range1d(min_x, max_x), 
              y_range=Range1d(min_y, max_y),
              plot_width=700)

p.xaxis[0].formatter = NumeralTickFormatter(format='0a')

text_x = 15000
text_y = 20

for i, group in enumerate(groups):
    p.add_glyph(Text(x=text_x, 
                     y=text_y, 
                     text=[group], 
                     text_font_size='10pt', 
                     text_color='#666666'))
    p.add_glyph(Circle(x=text_x - 2000, 
                       y=text_y + 1, 
                       fill_color=Spectral6[i], 
                       size=10, 
                       line_color=None, fill_alpha=0.8))
    text_y = text_y - 3

callback = CustomJS(args=dict(source=source), code="""
        var data = source.get('data');
        var v = cb_obj.get('value')
        x = data['gdp_' + v];
        y = data['lex_' + v];
        data['x'] = x;
        data['y'] = y;
        data['size'] = data['size_' + v];
        data['pop'] = data['pop_' + v];
        source.trigger('change');
    """)

p.scatter('x', 
          'y',
          source=source,
          size='size',
          fill_color=colors,
          fill_alpha=0.8)

slider = Slider(start=1800, end=2015, value=2015, step=1, title="Year",
                callback=callback)


layout = vform(p, slider)

bk.output_file("gdp_lex_gapminder.html")

bk.show(layout)
