import os, os.path as osp, pprint, re
import uproot
import numpy as np
import event as E


def single_pdata_to_file(
    outfile, pdata, mode='w', title=None, width=900, height=None, include_plotlyjs='cdn'
    ):
    import plotly.graph_objects as go
    scene = dict(xaxis_title='z (cm)', yaxis_title='x (cm)', zaxis_title='y (cm)', aspectmode='cube')
    if height is None: height = width
    fig = go.Figure(data=pdata, **(dict(layout_title_text=title) if title else {}))
    fig.update_layout(width=width, height=height, scene=scene)
    fig_html = fig.to_html(full_html=False, include_plotlyjs=include_plotlyjs)
    print('Writing to', outfile)
    outdir = osp.dirname(osp.abspath(outfile))
    if not osp.isdir(outdir): os.makedirs(outdir)
    with open(outfile, mode) as f:
        f.write(fig_html)


def fix_depth_recursively(node):
    """
    Traverses tree and makes sure child.depth > parent.depth
    """
    is_updated = False
    if node.parents:
        new_depth = max(p.depth for p in node.parents) + 1
        is_updated = node.depth != new_depth
        node.depth = new_depth
    for child in node.children:
        is_updated = is_updated or fix_depth_recursively(child)
    return is_updated


class EventException(Exception):
    pass

def zprime_3d_pdata(event):
    particles = event.particles.highest_status_zprime_descendants()

    if not particles:
        print(event.particles)
        print(event.particles.pid)
        raise EventException(
            f'Could not find a highest status zprime in event {event.index}'
            f'; {np.sum(event.particles.pid==4900023)=}'
            )

    # Filter out the fake 51/53 particles and mark their parent as stable dark hadron
    for p in particles: p.is_stable_hadron = False
    for p in particles:
        if abs(p.pid) in {51, 53}:
            for parent in p.parents:
                parent.is_stable_hadron = True
                parent.is_leaf = True
    particles = [p for p in particles if abs(p.pid) not in {51, 53}]

    # Fix the depth of the particles so that child.depth > parent.depth
    while fix_depth_recursively(particles[0]):
        pass

    # Group particles by category title for plotting purposes
    propwheel = E.PropertyWheel()
    propwheel.assign('stabledarkhadron', 'purple', 'Stable dark hadron')

    particles_by_title = {}
    for p in particles:
        p.color, p.title = propwheel('stabledarkhadron' if p.is_stable_hadron else abs(p.pid))
        particles_by_title.setdefault(p.title, [])
        particles_by_title[p.title].append(p)

    # Prepare pdata
    import plotly.graph_objects as go
    pdata = []

    # Avoid messing up the plot due to crazy eta numbers
    limit_eta = lambda eta: min(max(eta, -8.), 8.)
    
    # Plotting dot size: Initial particle is biggest, leafs are big
    def make_size(p):
        if p == particles[0]:
            return 9.
        elif p.is_leaf:
            return 7.
        else:
            return 4.

    for title, this_particles in particles_by_title.items():
        example_p = this_particles[0]
        etas = [limit_eta(p.eta) for p in this_particles]
        phis = [p.phi for p in this_particles]
        depths = [p.depth for p in this_particles]
        sizes = [make_size(p) for p in this_particles]
        texts = [
            f'index={p.index}'
            f'<br>pid={p.pid}<br>status={p.status}'
            f'<br>parents={", ".join([str(parent.index) for parent in p.parents])}'
            f'<br>eta={p.eta:.2f}<br>phi={p.phi:.2f}<br>pt={p.pt:.2f}<br>e={p.e:.2f}'
            # f'<br>x={p.x}<br>y={p.y}<br>z={p.z}'
            for p in this_particles
            ]
        pdata.append(go.Scatter3d(
            x=depths, y=etas, z=phis,
            marker=dict(
                line=dict(width=0),
                size=sizes,
                color=example_p.color,
                ),
            name =example_p.title,
            mode='markers',
            line=dict(width=0),
            text=texts,
            hovertemplate='%{text}',
            legendgroup=example_p.title
            ))

        # Edges - one by one unfortunately
        for p in this_particles:
            if p == particles[0]: continue
            if not p.parents: continue
            for parent in p.parents:
                pdata.append(go.Scatter3d(
                    x=[p.depth, parent.depth],
                    y=[limit_eta(p.eta), limit_eta(parent.eta)],
                    z=[p.phi, parent.phi],
                    marker=dict(size=0.),
                    line=dict(width=1., color=p.color),
                    mode='lines',
                    hoverinfo='skip',
                    legendgroup=p.title,
                    showlegend=False
                    ))
    
    return pdata


def dump_fig(outfile, fig, mode='w'):
    fig_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
    print(f'Writing to {outfile}, {mode=}')
    outdir = osp.dirname(osp.abspath(outfile))
    if not osp.isdir(outdir): os.makedirs(outdir)
    with open(outfile, mode) as f:
        f.write(fig_html)


def eventdisplay_3d():
    import plotly.graph_objects as go

    for rootfile in [
        'Nc3Nf3_sFoff_pp_1pi_decay_lam_10_probvec_75_0_R08_cut_200.root',
        'Nc3Nf3_sFoff_pp_1pi_decay_lam_10_probvec_05_0_R08_cut_200.root'
        ]:
        probvec = re.search(r'probvec_(\d+)', rootfile).group(1)
        ttree = uproot.open(rootfile)['Delphes']

        for i in range(25):
            try:
                event = E.get_event(ttree, i=i)
                pdata = zprime_3d_pdata(event)
                fig = go.Figure(data=pdata)
                fig.update_layout(
                    width=900, height=600,
                    scene=dict(
                        xaxis_title='Decay tree depth', yaxis_title='eta', zaxis_title='phi',
                        # aspectmode='cube'
                        )
                    )
                dump_fig(f'plots/probvec{probvec}_3d_{i//5}.html', fig, mode='w' if i%5==0 else 'a')
            except Exception as e:
                print(f'Failed for event {i}; Error:\n{e}')





        






















if __name__ == '__main__':
    eventdisplay_3d()
