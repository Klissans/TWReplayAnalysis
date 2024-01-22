from IPython.display import display, Markdown, Latex, Image, HTML
import plotly.express as px
import plotly.graph_objects as go

import numpy as np


br = '<br>'
bold = lambda x: f'<b>{x}</b>'
italic = lambda x: f'<i>{x}</i>'
img_local = lambda src, alt: f'''<img src="{src}" alt="{alt}" style="display:inline;margin:1px">'''
img_api = lambda src, alt: f'''<img src="https://res.cloudinary.com/fishofstone/image/upload/twwstats/api/6009914752132233841/{src}" alt="{alt}" style="display:inline;margin:1px">'''
img = lambda src, alt: img_local(src, alt)
h = lambda i, x: f'<h{i}>{x}</h{i}>'



class RAFormatter:
    
    def __init__(self, replay_analyser, default_template):
        self.default_template = default_template
        self.alliance_colors = ['red', 'blue', 'green', 'purple']
        self.army_colors = [
            ['red', 'darkred', 'palevioletred'],
            ['blue', 'darkblue', 'lightskyblue'],
            ['green', 'darkgreen', 'lightgreen'],
            ['purple', 'mediumpurple', 'rebeccapurple'],
        ]
        self.alliance_colors_mapping = {}
        self.army_colors_mapping = {}
        
        self._ra = replay_analyser
        self._generate_army_names()
        self._generate_alliances_names()
        self.set_color_mapping()
    
    def set_color_mapping(self):
        armies_df = self._ra._data['armies']
        for alliance_id in self._ra._data['alliances'].index:
            self.alliance_colors_mapping[alliance_id] = self.alliance_colors[alliance_id]
            for i, army_id in enumerate(armies_df[armies_df['alliance_id'] == alliance_id].index.get_level_values('unique_id').unique()):
                self.army_colors_mapping[army_id] = self.army_colors[alliance_id][i]
        pass
    
    def _generate_army_names(self):
        self.army_names = {}
        armies_df = self._ra._data['armies']
        for alliance_id in self._ra._data['alliances'].index:
            for army_id, row in armies_df[armies_df['alliance_id'] == alliance_id].iterrows():
                fpath = f"{row['flag_path']}/mon_24.png"
                # md += f"{img(fpath, row['faction_key'])} {row['PlayerName']} ({row['FactionName']})" + br
                self.army_names[army_id] = f"{row['PlayerName']} ({row['FactionName']})"
        return
    
    def _generate_alliances_names(self):
        
        self.alliance_names = {}
        armies_df = self._ra._data['armies']
        for alliance_id in self._ra._data['alliances'].index:
            md = []
            for army_id, row in armies_df[armies_df['alliance_id'] == alliance_id].iterrows():
                md.append(self.army_names[army_id])
            self.alliance_names[alliance_id] = ' | '.join(md)
        return
    
    def versus_screen(self):
        md = ''
        armies_df = self._ra._data['armies']
        units_df = self._ra._data['units']
        for alliance_id in self._ra._data['alliances'].index:
            md += h(1, f'Alliance #{alliance_id}') + br
            for army_id, row in armies_df[armies_df['alliance_id'] == alliance_id].iterrows():
                md += h(2, f"{row['PlayerName']} ({row['FactionName']})") + br
                fpath = f"{row['flag_path']}/mon_256.png"
                md += f'''{img(fpath, row['faction_key'])} '''
                army_units_df = units_df[units_df['ArmyID'] == army_id]
                # Main Army
                for j, urow in army_units_df[~army_units_df['is_reinforcement'] & ~army_units_df['is_appeared_mid_battle']].iterrows():
                    md += f'''{img(urow['IconPath'], urow['Name'])}'''
                md += br
                # Reinforcements
                md += h(3, 'Reinforcements')
                for j, urow in army_units_df[army_units_df['is_reinforcement']].iterrows():
                    md += f'''{img(urow['IconPath'], urow['Name'])}'''
                md += br
                # Spawned units
                if army_units_df[army_units_df['is_appeared_mid_battle']].shape[0] == 0:
                    continue
                md += h(3, 'Spawned')
                for j, urow in army_units_df[army_units_df['is_appeared_mid_battle']].iterrows():
                    md += f'''{img(urow['IconPath'], urow['Name'])}'''
            md += br*3
        return display(HTML(md))
    
    def _get_x_axis_time_s_min_max(self):
        return [self._ra._x_axis_time_s[0], self._ra._x_axis_time_s[-1]]

    def x_axis_time_ticks(self, step_seconds=30):
        _, mx = self._get_x_axis_time_s_min_max()
        vals = [x for x in np.arange(0, mx, step_seconds)]
        texts = [f'{x//60:.0f}:{x%60:02.0f}' for x in vals]
        xaxis = dict(
            tickmode='array',
            tickvals=vals,
            ticktext=texts,
        )
        return xaxis

    def battle_fought_time(self):
        ts = self._ra.battle_length_ms / 1000
        return display(Markdown(f"## Battle Fought for {ts//60:.0f}m {ts%60:.1f}s"))
    
    def plot_tickets(self):
        fig = go.Figure(layout_xaxis_range=self._get_x_axis_time_s_min_max())
        for i in self._ra._data['battle_alliances'].index.get_level_values('Id').unique():
            xs = self._ra._data['battle_alliances'].xs(i, level='Id')
            line = dict(color=self.alliance_colors_mapping[i])
            fig.add_trace(go.Scatter(x=xs['time_s'], y=xs['TicketsRemaining'], fill='tozeroy', line=line, name=self.alliance_names[i]))
        fig.update_layout(title='Tickets over Time', legend=dict(orientation="h"), xaxis=self.x_axis_time_ticks(), template=self.default_template)
        fig.update_xaxes(title=dict(text='Time(s)'))
        fig.update_yaxes(title=dict(text='Tickets'))
        return fig
    
    def calculate_average_supply(self):
        avg_supplies = {}
        battle_armies_df = self._ra._data['battle_armies']
        for i in battle_armies_df.index.get_level_values('unique_id').unique():
            xs = battle_armies_df.xs(i, level='unique_id')
            gc_sum = xs['GlobalCurrency'].sum()
            avg_supplies[i] = gc_sum / (xs.shape[0])
        return avg_supplies
    
    def plot_supplies(self):
        battle_armies_df = self._ra._data['battle_armies']
        fig = go.Figure(layout_xaxis_range=self._get_x_axis_time_s_min_max())
        for i in battle_armies_df.index.get_level_values('unique_id').unique():
            xs = battle_armies_df.xs(i, level='unique_id')
            color = self.army_colors_mapping[i]
            line = dict(color=color)
            fig.add_trace(go.Scatter(x=xs['time_s'], y=xs['GlobalCurrency'], line=line, name=self.army_names[i]))
            avg_supply = xs['GlobalCurrency'].sum() / (xs.shape[0])
            line = dict(dash='dash', color=color)
            fig.add_trace(go.Scatter(x=xs['time_s'], y=[avg_supply]*xs.shape[0], line=line, name=self.army_names[i] + f' avg supply: {avg_supply:.0f}'))
        fig.update_layout(title='Supplies over Time', legend=dict(orientation="h"), xaxis=self.x_axis_time_ticks(), template=self.default_template)
        fig.update_xaxes(title=dict(text='Time(s)'))
        fig.update_yaxes(title=dict(text='Supplies'))
        return fig
        
        
    def plot_wom(self):
        fig = go.Figure(layout_xaxis_range=self._get_x_axis_time_s_min_max())
        for i in self._ra._data['battle_armies'].index.get_level_values('unique_id').unique():
            xs = self._ra._data['battle_armies'].xs(i, level='unique_id')
            line = dict(color=self.army_colors_mapping[i])
            fig.add_trace(go.Scatter(x=xs['time_s'], y=xs['winds_of_magic_current'], line=line, name=self.army_names[i]))
        fig.update_layout(title='Winds of Magic over Time', legend=dict(orientation="h"), xaxis=self.x_axis_time_ticks(), template=self.default_template)
        fig.update_xaxes(title=dict(text='Time(s)'))
        fig.update_yaxes(title=dict(text='WoM'))
        return fig
    
    def interact_unit_stat(self):
        uinfo_df = self._ra._data['units']
        uniqs = uinfo_df.index.get_level_values('unique_ui_id').unique()
        unit_names = [f"{uinfo_df.loc[u, 'Name']} [{u}]" for u in uniqs]
        cols = ['BattleResult.DamageDealt', 'BattleResult.DamageDealtCost', 'BattleResult.NumKillsFriendlies', 'NumKills']
        
        fig = go.FigureWidget(layout_xaxis_range=self._get_x_axis_time_s_min_max())
        fig.add_scatter() # original stats
        # fig.add_scatter() # interpolated dash
        def f(unit_name, stat):
            unit_id = int(unit_name.split('[')[1].split(']')[0])
            xs = self._ra._data['battle_units'].xs(unit_id, level='unique_ui_id')
            unit = self._ra._data['units'].loc[unit_id]
            color = self.army_colors_mapping[unit['ArmyID']]
            with fig.batch_update():
                fig.data[0].x = self._ra._x_axis_time_s
                fig.data[0].y = self._ra._fill_linear(xs[stat].fillna('None'))
                fig.data[0].line.color = color
                fig.update_xaxes(title=dict(text='Time(s)'))
                fig.update_yaxes(title=dict(text=stat))
                fig.update_layout(title=f'{stat} over Time for {unit_name}', legend=dict(orientation="h"), xaxis=self.x_axis_time_ticks(), template=self.default_template)
            return fig
        return unit_names, cols, f