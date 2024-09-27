from dataclasses import dataclass, field

import numpy as np

import constants
import random


@dataclass
class UE:
    pk: int
    Data_Size_Du: float  # Data size in MB
    Computation_Resource_fu: float  # Required computation resources in GHz
    Max_Latency_Tmax_u: float  # Maximum allowed latency in seconds
    Local_Computing_Capacity_clocalu: float  # CPU cycles in GHz
    Transmission_Power_Pu: float  # Transmission power in watts
    Average_Sojourn_Time_tau: dict[int, float] = field(default_factory=dict)  # Average sojourn time in seconds
    Uplink_Rate_r: dict[int, float] = field(default_factory=dict)  # Uplink rate in Mbps

    def __post_init__(self):
        if not self.Uplink_Rate_r:
            self.Uplink_Rate_r = {i+1: random.random() * 10 + 1 for i in range(constants.F)}
        if not self.Average_Sojourn_Time_tau:
            self.Average_Sojourn_Time_tau = {i+1: random.randint(10, 30) for i in range(constants.F)}

    @property
    def T_local(self) -> float:
        return self.Computation_Resource_fu / self.Local_Computing_Capacity_clocalu

    @property
    def E_local(self) -> float:
        return constants.κ * self.Local_Computing_Capacity_clocalu ** 2 * self.Computation_Resource_fu

    @property
    def Q_local(self) -> float:
        return constants.λEu * self.E_local + constants.λTu * self.T_local

    def get_Average_Sojourn_Time_tauuf(self, fcn_id) -> float:
        return self.Average_Sojourn_Time_tau[fcn_id]

    def get_Uplink_Rate_ruf(self, fcn_id) -> float:
        return self.Uplink_Rate_r[fcn_id]

    def get_t_up_uf(self, fcn_id):
        return self.Data_Size_Du / self.get_Uplink_Rate_ruf(fcn_id=fcn_id)

    def get_t_exe_uf(self, computation_capacity_cuf):
        return self.Computation_Resource_fu / computation_capacity_cuf

    def get_T_F_uf(self, fcn_id,  computation_capacity_cuf):
        t_exec_uf = self.get_t_exe_uf(computation_capacity_cuf)
        return self.get_t_up_uf(fcn_id) + t_exec_uf

    def get_E_up_uf(self, fcn_id):
        return self.Transmission_Power_Pu * self.get_t_up_uf(fcn_id)

    def get_q_F_uf(self, fcn_id, computation_capacity_cuf):
        return constants.λEu * self.get_E_up_uf(fcn_id) + constants.λTu * self.get_T_F_uf(
            fcn_id, computation_capacity_cuf
        )

    def get_q_mig_u(self):
        return constants.δ * self.Data_Size_Du

    def get_P_t_s_uf_gt_T_F_uf(self, fcn_id, computation_capacity_cuf):
        sojourn_time = self.Average_Sojourn_Time_tau[fcn_id]
        return np.exp(-self.get_T_F_uf(fcn_id, computation_capacity_cuf) / sojourn_time)

    def get_P_t_s_uf_le_T_F_uf(self, fcn_id, computation_capacity_cuf):
        return 1 - self.get_P_t_s_uf_gt_T_F_uf(fcn_id, computation_capacity_cuf)

    def get_q_bar_F_uf(self, fcn_id, computation_capacity_cuf):
        return self.get_P_t_s_uf_gt_T_F_uf(fcn_id, computation_capacity_cuf) * self.get_q_F_uf(
            fcn_id, computation_capacity_cuf
        ) + self.get_P_t_s_uf_le_T_F_uf(fcn_id, computation_capacity_cuf) * (
            self.get_q_F_uf(fcn_id, computation_capacity_cuf) + self.get_q_mig_u()
        )

    def get_Quf(self, fcn_id, computation_capacity_cuf):
        return self.Q_local - self.get_q_bar_F_uf(fcn_id, computation_capacity_cuf)


@dataclass
class FCN:
    pk: int
    Computing_Capacity_cF: dict[int, float] = field(default_factory=dict)  # Computing capacity in GHz

    
    def __post_init__(self):
        if not self.Computing_Capacity_cF:
            self.Computing_Capacity_cF = {i+1: random.random() * 100 for i in range(constants.U)}
    
    @property
    def cF(self) -> float:
        return sum(self.Computing_Capacity_cF.values()) + 1
    