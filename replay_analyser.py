import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

from utils import *


class ReplayAnalyser:
    static_tables = ['info', 'alliances', 'armies', 'units']
    dynamic_tables = ['battle_alliances', 'battle_armies', 'battle_units']
    
    def __init__(self, settings):
        self._meta = {}
        self._settings = settings
        self._load_all_data()
        pass

    
    def _get_full_path_to_replay(self):
        return os.path.join(self._settings['path_to_replay_dumps'], self._settings['replay_name'])
    
    def _read_info(self):
        self.battle_info = {}
        row = self._data['info'].iloc[0]
        self.battle_info['IsDomination'] = row['IsDomination']
    
    def _load_all_data(self, sep='|'):
        path = self._get_full_path_to_replay()
        tables = self.static_tables + self.dynamic_tables
        self._data = {}
        for tname in tables:
            self._data[tname] = pd.read_csv(f'{path}{tname}.csv', sep=sep, low_memory=False, na_values=['nil'])
        self._read_info()
        if self.battle_info['IsDomination']:
            self._data['reinforcement_armies'] = pd.read_csv(f'{path}reinforcement_armies.csv', sep=sep, low_memory=False, na_values=['nil'])
            self._data['reinforcement_armies']['target_army_id'] = self._data['reinforcement_armies']['alliance_id']
            self._data['reinforcement_armies'].drop(['alliance_id'], axis=1, inplace=True)
            self._data['reinforcement_armies'].set_index('unique_id', drop=False, inplace=True)
        self._preprocess_data()
        self._adjust_time()
        self._set_ids()

    def _adjust_time(self):
        for tname in dynamic_tables:
            time_delay = self._data[tname]['time'].min()
            self._deployment_phase_time = to_s(time_delay)
            self._data[tname]['time'] = self._data[tname]['time'] - time_delay
            self._data[tname]['time_s'] = self._data[tname]['time'].apply(to_s)
            self.battle_length_ms = self._data[tname]['time'].max()

        self._x_axis_time_s = np.sort(self._data['battle_alliances']['time_s'].unique())
        self._x_axis_time = np.sort(self._data['battle_alliances']['time'].unique())
            
    def _set_ids(self):
        self._data['alliances'].set_index('Id', drop=False, inplace=True)
        self._data['armies'].set_index('unique_id', drop=False, inplace=True)
        self._data['units'].set_index('unique_ui_id', drop=False, inplace=True)
        self._data['battle_alliances'].set_index(['Id', 'time'], drop=False, inplace=True)
        self._data['battle_armies'].set_index(['unique_id', 'time'], drop=False, inplace=True)
        self._data['battle_units'].set_index(['unique_ui_id', 'time'], drop=False, inplace=True)
        
    def _preprocess_data(self):
        self._preprocess_battle_units()
    
    def _preprocess_battle_units(self):
        bu_df = self._data['battle_units']
        for col in bu_df.select_dtypes(include=[np.int64]).columns:
            mn = bu_df[col].min()
            mx = bu_df[col].max()
            if mn == 0 and mx == 1:
                bu_df[col] = bu_df[col].astype(bool)
        
        self._data['battle_units'] = bu_df[~bu_df['is_reinforcement']]

        int_cols = ['HealthValue', 'NumEntities', 'ExperienceLevel', 'MoraleState', 'FatigueState', 'NumKills', 'BarrierHp', 'BarrierMaxHp', 'ammo_left', 'number_of_enemies_killed']
        int_cols += ['BattleResult.DamageDealt', 'BattleResult.DamageDealtCost', 'BattleResult.NumHitPoints', 'BattleResult.NumKillsFriendlies']
        for col in int_cols:
            bu_df[col] = bu_df[col].astype(np.float32)
            
        float_cols = ['MoralePercent', 'MaxHealthPercentCanReplenish', 'BarrierHpPercent', 'BarrierCapPercent', 'HealthPercent']
        for col in float_cols:
            bu_df[col] = bu_df[col].astype(np.float32)
        return
    
    def _fill_linear(self, series):
        l = self._x_axis_time_s.shape[0]
        s = pd.Series([None]*l, index=self._x_axis_time)
        s.loc[series.index] = series
        return s
        
    def is_domination(self):
        return self.battle_info['IsDomination']
        