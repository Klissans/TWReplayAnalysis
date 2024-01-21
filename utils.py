import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from IPython.display import display, Markdown, Latex, Image


static_tables = ['info', 'alliances', 'armies', 'units']
dynamic_tables = ['battle_alliances', 'battle_armies', 'battle_units']


def show_md(s):
    return display(Markdown(s))


def to_s(ms):
    return ms / 1000.0
    
        