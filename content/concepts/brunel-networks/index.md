---
title: Brunel networks
date: 2026-09-07
draft: false
---
These are working notes from the summer school on **Advanced tools for data analyses in neuroscience**, and from the summer-school project I worked on with **Julie and Ebru, supervised by Dr. Jyotika Bahuguna**. 

## 1. Starting with a LIF neuron

The neurons in our simulation are leaky integrate-and-fire units. In my Brian2 notebook,

$$
\frac{dv}{dt}=\frac{-v+s_e+s_i+I_{\mathrm{mod}}(t)-w}{\tau_m}.
$$

A spike occurs when $v>V_\theta$, after which $v\leftarrow V_r$.

For this simulation, $\tau_m=20$ ms, $V_\theta=20$ mV, $V_r=10$ mV, the refractory period is 2 ms, and the synaptic delay is 1.5 ms.

One point from Jyotika's lecture that I want to remember is that a reduced model is a choice. LIF ignores ion-channel dynamics, dendrites and spike shape, but keeps the ingredients needed for the population-level question here.

## 2. Synaptic dynamics

Excitatory and inhibitory input are represented by

$$
\frac{ds_e}{dt}=-\frac{s_e}{\tau_{\mathrm{syn}}},\qquad
\frac{ds_i}{dt}=-\frac{s_i}{\tau_{\mathrm{syn}}}.
$$

For an excitatory presynaptic spike,

$$
s_e\leftarrow s_e+J,
$$

and for an inhibitory spike,

$$
s_i\leftarrow s_i-gJ.
$$

Here $J=0.1$ mV and $g$ is the inhibitory-to-excitatory synaptic weight ratio. In these notes, $g$ therefore means **relative inhibitory strength**, not membrane conductance.

## 3. The recurrent E/I population

The network contains

$$
N_E=2000,\qquad N_I=500,
$$

so $N=2500$ and the E:I population ratio is 4:1. Connections are random with probability

$$
\epsilon=0.1.
$$

A rough sketch:

```text
                      Poisson drive
                           |
                           v
               +-----------------------+
|  |
           +-------+               +-------+
| E | --------------> | I |
| 2000 | <-------------- | 500 |
           +-------+               +-------+
              \                       /
               \_____ recurrent _____/
```

Both recurrent activity and stochastic external bombardment therefore contribute to the fluctuations seen by a neuron.

## 4. External drive

The notebook defines

$$
C_{\mathrm{ext}}=\epsilon N_E
$$

and

$$
\nu_{\mathrm{thr}}=
\frac{V_\theta}{J C_{\mathrm{ext}}\tau_m},
$$

then scales the actual Poisson rate as

$$
\nu_{\mathrm{ext}}=\mathrm{inputlevel}\nu_{\mathrm{thr}}.
$$

In our presentation, this was described as 200 independent input streams per neuron, with each event adding $J=0.1$ mV.

## 5. Synchrony and regularity

I initially kept mixing these up.

**Synchrony** is a population-level property: are neurons tending to spike together?

**Regularity** is a single-neuron property: are its inter-spike intervals regular?

So asynchronous-irregular (AI) and synchronous-irregular (SI) are perfectly sensible combinations. A messy individual spike train does not imply that the population has no collective temporal structure.

## 6. The phase diagram from the lecture

This was probably the figure that made the model click for me.

Dr. Bahuguna's lecture organised network regimes using two important controls: the relative inhibitory strength $g$ and the external drive $\nu_{\mathrm{ext}}$. The point is not merely that these parameters change firing rate; moving through parameter space can change the **qualitative network state**.

My schematic recollection is:

```text
 external drive
       ^
       |
 high  |       SR                    SI fast
       |         \                  /
       |          \       AI       /
       |           \              /
       |            \____________/
       |                  \
 low   |                   SI slow
       |
       +------------------------------------> g
                    stronger inhibition
```

**This is a schematic redraw from my notes, not a digitisation of the numerical boundaries in the lecture slide.**

The lecture discusses synchronous regular (SR), asynchronous irregular (AI), and synchronous irregular regimes. Reduced inhibition with high input favours strongly synchronous/regular activity; high inhibition with high drive can strongly entrain the network; high inhibition with lower drive gives weaker/slower entrainment.

The part I want to remember is:

> E/I balance is not simply a gain knob. It can move a recurrent network between qualitatively different dynamical regimes.

## 7. Adaptation

We also added

$$
\frac{dw}{dt}=-\frac{w}{\tau_m},
$$

with a spike-triggered update

$$
w\leftarrow w+w_{\mathrm{adapt}}.
$$

Because $w$ enters the membrane equation negatively, repeated firing builds temporary negative feedback.

## 8. Our summer project

Our project was **Parameter-Dependent Emergent Oscillatory Dynamics in Recurrent Excitatory-Inhibitory Networks**, by **Vinay, Julie & Ebru**, supervised by **Dr. Jyotika Bahuguna**.

We mainly played with

$$
g,\qquad \tau_{\mathrm{syn}},\qquad w_{\mathrm{adapt}},
$$

and asked how changing them altered the oscillatory population activity.

## 9. Looking in frequency space

From the population firing rate $r(t)$, the notebook removes the initial transient and mean,

$$
\tilde r(t)=r(t)-\langle r(t)\rangle,
$$

then computes

$$
R(f)=\mathcal{F}\tilde r(t).
$$

Conceptually:

```text
spikes
  |
  v
population rate r(t)
  |
  | remove transient + mean
  v
r(t) - <r>
  |
  | FFT
  v
amplitude spectrum
```

One methodological point I want to keep explicit: the main `create_amplitude_spectrum()` function uses constant-rate stochastic Poisson input with **no sinusoidal modulation**. It is therefore asking what spectral structure emerges in recurrent activity. The notebook separately contains sinusoidally modulated input; a driven transfer-function experiment is related, but not identical.

## 10. Changing inhibitory strength

In the range we explored, the response was non-monotonic in $g$. A particularly strong oscillatory response occurred around

$$
g=4.5,
$$

with a prominent frequency around

$$
f\sim20\ \mathrm{Hz}.
$$

I do not interpret $g=4.5$ as a universal optimum. It is a result for this model and parameter range. The interesting part is that "more inhibition" does not map monotonically onto "less activity". This connects naturally to the phase-diagram picture.

## 11. Changing the synaptic time constant

Increasing $\tau_{\mathrm{syn}}$ kept the dominant frequency relatively stable over much of the tested range, while the spectral peak became flatter. At very large values the neurons seemed less able to entrain as a network.

My naive expectation had been closer to "longer synaptic time constant = lower preferred frequency", so this was a useful reminder that membrane, synaptic and recurrent-network timescales interact.

The notebook also repeats runs across random realisations for 5, 10, 20 and 50 ms conditions rather than relying on one stochastic simulation.

## 12. Changing adaptation

Increasing adaptation reduced response amplitude and shifted the preferred population frequency downward.

Qualitatively, spike-triggered negative feedback makes sustained rapid firing harder. What I have not separated yet is whether the frequency shift comes directly from adaptation dynamics or partly from the accompanying change in mean firing rate.

## 13. Things I want to try next

- Reproduce the $g$ versus $\nu_{\mathrm{ext}}$ phase diagram systematically.
- Define numerical criteria for AI, SI and SR rather than classifying raster plots by eye.
- Compare coefficient of variation of ISIs with a population synchrony measure.
- Give E and I synapses different time constants.
- Compare spontaneous spectra with a proper sinusoidal frequency-response experiment.
- Test stability across random network realisations.
- Give adaptation its own time constant.
- Compare this current-like implementation with a conductance-based network.

For me this is the useful part of the Brunel network: the individual equations are simple enough to understand, but their recurrent interaction is already complicated enough to produce behaviour I would not confidently predict beforehand.

---

## Notebook

[Download the Brian2 notebook](/notebooks/brunel_network_amplitude_spectrum_hands_on.ipynb)

[Open in Google Colab](https://colab.research.google.com/github/Vinay-Neuro/Vinay-Neuro.github.io/blob/main/static/notebooks/brunel_network_amplitude_spectrum_hands_on.ipynb)

## Attribution

These notes are based primarily on **Dr. Jyotika Bahuguna's *Introduction to Neurocomputational Modeling* lecture / neuronal-circuits modelling material (FunDyn 2026)** and the associated hands-on exercise.

The simulation discussion comes from our 2026 summer-school project ***Parameter-Dependent Emergent Oscillatory Dynamics in Recurrent Excitatory-Inhibitory Networks***, by **Vinay, Julie & Ebru**, supervised by **Jyotika Bahuguna**.

The phase diagram above is my own schematic redraw/summary rather than a copied lecture figure.