# Setup

```
python3 -m venv env
source env/bin/activate

pip install uproot
pip install plotly
```

# Data

Currently the code is using these two files:

```
wget https://www.dropbox.com/sh/z4gtjgfet408w1w/AABmnbtysaAfSSNzMnNgAsLfa/v2_samples_R08_cut_200/pythia_8307_R_08_cut_200/probvec_75/Nc3Nf3_sFoff_pp_1pi_decay_lam_10_probvec_75/Nc3Nf3_sFoff_pp_1pi_decay_lam_10_probvec_75_0_R08_cut_200.root

wget https://www.dropbox.com/sh/z4gtjgfet408w1w/AAChbpylF5rE2vgOZxFeqmPga/v2_samples_R08_cut_200/pythia_8307_R_08_cut_200/probvec_05/Nc3Nf3_sFoff_pp_1pi_decay_lam_10_probvec_05/Nc3Nf3_sFoff_pp_1pi_decay_lam_10_probvec_05_0_R08_cut_200.root
```

We should look at other files in https://www.dropbox.com/sh/z4gtjgfet408w1w/AADA1QoR6kX1Lkq0IUo5nI-ea/v2_samples_R08_cut_200/pythia_8307_R_08_cut_200 as well.


# Run

```python displays.py```
