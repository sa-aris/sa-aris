<!-- ====================== HEADER ====================== -->
<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/sa-aris/sa-aris/main/assets/hero-dark.svg" />
  <img alt="Aris — software engineer who simulates brains. A small spiking network fires activity cascades while a simulated neuron's membrane potential sweeps across the bottom." src="https://raw.githubusercontent.com/sa-aris/sa-aris/main/assets/hero-light.svg" width="100%" />
</picture>

<a href="https://github.com/sa-aris">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=500&size=18&pause=1200&color=58A6FF&center=true&vCenter=true&width=640&lines=Full-stack+%C2%B7+Mobile+%C2%B7+Data+%26+AI;Connectome-constrained+brain+simulation;Spiking+networks+%C2%B7+plasticity+%C2%B7+%CE%A6;Clean+code+for+messy+science" alt="Full-stack · Mobile · Data & AI — Connectome-constrained brain simulation — Spiking networks · plasticity · Φ" />
</a>

<sub><b>Keywords</b> — computational neuroscience · connectomics · spiking neural networks · synaptic plasticity · integrated information · full-stack · mobile</sub>

> *"I trust the unknown — it's the code I think I understand that scares me."*

</div>

<!-- ====================== ABSTRACT ====================== -->
## Abstract

I build software across the whole stack — web, mobile, data — and point it at one of the
hardest questions I know: **how does wiring become behaviour?** My main research project,
**Elegans**, takes real connectome data, turns it into a spiking neural network, lets
biologically plausible learning rules loose in a simulated ecosystem, and measures what
happens with tools from information theory. Everywhere else I write clean, dependable code
that ships: game-AI frameworks, shared memory for multi-agent LLM systems, cross-lingual
stylometry, and the apps that hold them together.

```python
class Aris(LIFNeuron):
    """Full-stack engineer · integrate-and-fire researcher."""

    tau_m     = "patient"                   # membrane time constant
    threshold = "a genuinely good question"  # fires when curiosity ≥ θ
    inputs    = ["TypeScript", "Python", "C++", "Kotlin", "Swift", "Java", "C#"]
    outputs   = ["web apps", "mobile apps", "brain simulations", "research tooling"]

    def step(self, problem):
        self.v += problem.difficulty        # integrate
        if self.v >= self.threshold:        # fire
            return self.ship(clean_code=True, tests=True)
        self.v *= 0.95                      # leak — but never forget
```

- 🔬 **Researching** connectome-constrained simulation, three-factor plasticity and integrated information (Φ).
- 🛠️ **Building** full-stack web apps, cross-platform mobile apps and tooling for data & scientific computing.
- 🌱 **Going deeper** across the TypeScript, Python and native-mobile ecosystems.
- 💬 **Ask me about** spiking networks, connectomics, full-stack architecture or data/AI workflows.

<!-- ====================== RESEARCH ====================== -->
## 1 · Research — *Elegans*

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/sa-aris/sa-aris/main/assets/elegans-dark.svg" />
  <img alt="Fig. 1 — Elegans. Left: a C. elegans nematode crawling up an odorant gradient on an agar plate. Right: the closed loop the project studies — connectome, spiking dynamics, behaviour, neuromodulation, plasticity — with integrated information Φ measured on the dynamics." src="https://raw.githubusercontent.com/sa-aris/sa-aris/main/assets/elegans-light.svg" width="100%" />
</picture>

<sub><b>Fig. 1</b> | The project is named after <i>C. elegans</i>, the first animal whose complete wiring
diagram was mapped<a href="#references"><sup>1</sup></a>. The question it asks: how much adaptive behaviour
emerges when a real animal's connectome is made to spike, learns with biologically plausible rules inside
a living ecosystem — and does integrated information track any of it?</sub>

| Layer | Approach |
|:--|:--|
| **Wiring** | Synapse-resolution connectomes — the *Drosophila* hemibrain<a href="#references"><sup>3</sup></a> and a 302-neuron *C. elegans* chemotaxis prototype<a href="#references"><sup>1,2</sup></a> |
| **Dynamics** | Spiking, integrate-and-fire neurons whose coupling comes straight from the anatomy |
| **Learning** | Several concurrent, biologically grounded rules: STDP and eligibility traces gated by neuromodulators<a href="#references"><sup>4</sup></a> |
| **World** | A multi-species ecological arena — foraging, predators, seasons, day and night |
| **Measurement** | Integrated information Φ, estimated with a Gaussian time-series proxy<a href="#references"><sup>5,6</sup></a> |

> [!NOTE]
> Elegans lives in a private repository while the research is in progress — code, data and
> results are not published here. The figure and equations above are illustrations of the
> textbook ideas it builds on.

<details>
<summary><b>The ideas in three equations</b></summary>

<br/>

**Leaky integrate-and-fire neuron** — membrane potential integrates weighted input spikes, leaks
back to rest, and emits a spike at threshold:

```math
\tau_m \frac{dV_i}{dt} = -\left(V_i - V_{\mathrm{rest}}\right) + R_m \sum_j w_{ij}\, s_j(t),
\qquad V_i \ge \theta \;\Rightarrow\; \text{spike},\; V_i \leftarrow V_{\mathrm{reset}}
```

**Three-factor plasticity**<a href="#references"><sup>4</sup></a> — STDP only *tags* a synapse with an
eligibility trace; a neuromodulatory signal $M(t)$ (reward, novelty, danger) decides whether the tag
becomes a weight change:

```math
\frac{de_{ij}}{dt} = -\frac{e_{ij}}{\tau_e} + \mathrm{STDP}\!\left(s^{\mathrm{pre}}_j, s^{\mathrm{post}}_i\right),
\qquad \Delta w_{ij} = \eta\, M(t)\, e_{ij}
```

**Integrated information**<a href="#references"><sup>5,6</sup></a> — how much the whole system's past
predicts its present *beyond* what its parts predict on their own, at the minimum-information
bipartition:

```math
\Phi = I\!\left(X_{t-\tau}; X_t\right) - \sum_{k} I\!\left(M^{k}_{t-\tau}; M^{k}_{t}\right)\Big|_{\mathrm{MIP}},
\qquad I(X;Y) = \tfrac{1}{2}\log\frac{\lvert\Sigma_X\rvert}{\lvert\Sigma_{X\mid Y}\rvert}
```

</details>

<!-- ====================== INTERESTS ====================== -->
## 2 · Interests

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/sa-aris/sa-aris/main/assets/interests-dark.svg" />
  <img alt="Fig. 2 — Periodic table of interests. Neuroscience: connectomics, spiking networks, plasticity, neuromodulation, integrated information, insect vision. Complex systems: neuroevolution, artificial life, multi-agent systems. Language and AI: stylometry, LLM memory, game AI. Engineering: scientific computing, full-stack, mobile, developer tooling." src="https://raw.githubusercontent.com/sa-aris/sa-aris/main/assets/interests-light.svg" width="100%" />
</picture>

<sub><b>Fig. 2</b> | Sixteen interests in four groups. The glow that walks across the table follows atomic
number — an excitation, not a ranking.</sub>

<!-- ====================== SELECTED WORKS ====================== -->
## 3 · Selected works

<div align="center">

<a href="https://github.com/sa-aris/aithena"><picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/sa-aris/sa-aris/output/card-aithena-dark.svg" />
  <img alt="aithena — C++17 NPC AI framework" src="https://raw.githubusercontent.com/sa-aris/sa-aris/output/card-aithena-light.svg" width="49%" />
</picture></a>
<a href="https://github.com/sa-aris/Context-Bridge"><picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/sa-aris/sa-aris/output/card-context-bridge-dark.svg" />
  <img alt="Context-Bridge — shared neural memory for multi-agent LLM systems" src="https://raw.githubusercontent.com/sa-aris/sa-aris/output/card-context-bridge-light.svg" width="49%" />
</picture></a>
<a href="https://github.com/sa-aris/idiolect"><picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/sa-aris/sa-aris/output/card-idiolect-dark.svg" />
  <img alt="idiolect — cross-lingual author attribution" src="https://raw.githubusercontent.com/sa-aris/sa-aris/output/card-idiolect-light.svg" width="49%" />
</picture></a>
<a href="https://github.com/sa-aris/cpp-rpg-inventory-system"><picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/sa-aris/sa-aris/output/card-cpp-rpg-inventory-system-dark.svg" />
  <img alt="cpp-rpg-inventory-system — modular RPG inventory backend in C++17" src="https://raw.githubusercontent.com/sa-aris/sa-aris/output/card-cpp-rpg-inventory-system-light.svg" width="49%" />
</picture></a>

</div>

<!-- ====================== METHODS ====================== -->
## 4 · Methods — toolchain

<div align="center">

**Languages**

![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Java](https://img.shields.io/badge/Java-ED8B00?style=for-the-badge&logo=openjdk&logoColor=white)
![C#](https://img.shields.io/badge/C%23-239120?style=for-the-badge&logo=dotnet&logoColor=white)
![C++](https://img.shields.io/badge/C++-00599C?style=for-the-badge&logo=cplusplus&logoColor=white)
![Kotlin](https://img.shields.io/badge/Kotlin-7F52FF?style=for-the-badge&logo=kotlin&logoColor=white)
![Swift](https://img.shields.io/badge/Swift-FA7343?style=for-the-badge&logo=swift&logoColor=white)

**Frontend**

![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-38B2AC?style=for-the-badge&logo=tailwindcss&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)

**Backend**

![Node.js](https://img.shields.io/badge/Node.js-339933?style=for-the-badge&logo=nodedotjs&logoColor=white)
![Express](https://img.shields.io/badge/Express-000000?style=for-the-badge&logo=express&logoColor=white)
![.NET](https://img.shields.io/badge/.NET-512BD4?style=for-the-badge&logo=dotnet&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Spring](https://img.shields.io/badge/Spring-6DB33F?style=for-the-badge&logo=spring&logoColor=white)

**Mobile**

![Android](https://img.shields.io/badge/Android-3DDC84?style=for-the-badge&logo=android&logoColor=white)
![Jetpack Compose](https://img.shields.io/badge/Jetpack%20Compose-4285F4?style=for-the-badge&logo=jetpackcompose&logoColor=white)
![SwiftUI](https://img.shields.io/badge/SwiftUI-0071E3?style=for-the-badge&logo=swift&logoColor=white)
![React Native](https://img.shields.io/badge/React%20Native-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)

**Data &amp; Scientific Computing**

![NumPy](https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white)
![SciPy](https://img.shields.io/badge/SciPy-8CAAE6?style=for-the-badge&logo=scipy&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white)
![Jupyter](https://img.shields.io/badge/Jupyter-F37626?style=for-the-badge&logo=jupyter&logoColor=white)

**Databases &amp; Tools**

![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Git](https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)
![Figma](https://img.shields.io/badge/Figma-F24E1E?style=for-the-badge&logo=figma&logoColor=white)

</div>

<!-- ====================== RESULTS ====================== -->
## 5 · Results — measured, not claimed

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/sa-aris/sa-aris/output/activity-dark.svg" />
  <img alt="Fig. 3 — Contribution activity over the last year drawn as a neural spike train: weekly histogram with a smoothed rate, a raster of daily contributions, and spike-train statistics." src="https://raw.githubusercontent.com/sa-aris/sa-aris/output/activity-light.svg" width="100%" />
</picture>

<sub><b>Fig. 3</b> | A year of contributions read the way a neuroscientist reads a neuron. <b>(a)</b> Weekly
peri-stimulus-style histogram with a Gaussian-smoothed rate, over a raster where every tick is a
contribution (amber = a burst of ten or more in one day). <b>(b)</b> Spike-train statistics<a href="#references"><sup>7</sup></a>:
the Fano factor and the inter-spike-interval CV both equal 1 for a Poisson process — above that, the work
comes in bursts.</sub>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/sa-aris/sa-aris/output/spectrum-dark.svg" />
  <img alt="Fig. 4 — Languages across public repositories drawn as emission lines on the visible spectrum, next to a table of GitHub observables." src="https://raw.githubusercontent.com/sa-aris/sa-aris/output/spectrum-light.svg" width="100%" />
</picture>

<sub><b>Fig. 4</b> | <b>(a)</b> Language mix across public repositories as an emission spectrum: each language
is a spectral line placed at the wavelength of its GitHub colour, its height set by its share of code.
<b>(b)</b> Observables. Figs. 3–5 are regenerated every 12 hours by <a href="https://github.com/sa-aris/sa-aris/blob/main/.github/workflows/snake.yml">a GitHub Action</a>
from <a href="https://github.com/sa-aris/sa-aris/tree/main/scripts">dependency-free scripts</a> in this repository.</sub>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/sa-aris/sa-aris/output/github-contribution-grid-snake-dark.svg" />
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/sa-aris/sa-aris/output/github-contribution-grid-snake.svg" />
  <img alt="Contribution snake animation eating the contribution graph" src="https://raw.githubusercontent.com/sa-aris/sa-aris/output/github-contribution-grid-snake.svg" width="100%" />
</picture>

<sub><b>Fig. 5</b> | The same data, less rigorously: a snake eats the contribution graph.</sub>

<!-- ====================== CONTACT ====================== -->
## 6 · Correspondence

<div align="center">

<a href="mailto:solus.aris@proton.me"><img alt="Email" src="https://img.shields.io/badge/Email-8B89CC?style=for-the-badge&logo=protonmail&logoColor=white" /></a>
<a href="https://github.com/sa-aris"><img alt="GitHub" src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white" /></a>

</div>

<!-- ====================== REFERENCES ====================== -->
## References

1. White, J. G., Southgate, E., Thomson, J. N. & Brenner, S. The structure of the nervous system of the nematode *Caenorhabditis elegans*. *Phil. Trans. R. Soc. Lond. B* **314**, 1–340 (1986). [doi:10.1098/rstb.1986.0056](https://doi.org/10.1098/rstb.1986.0056)
2. Cook, S. J. *et al.* Whole-animal connectomes of both *Caenorhabditis elegans* sexes. *Nature* **571**, 63–71 (2019). [doi:10.1038/s41586-019-1352-7](https://doi.org/10.1038/s41586-019-1352-7)
3. Scheffer, L. K. *et al.* A connectome and analysis of the adult *Drosophila* central brain. *eLife* **9**, e57443 (2020). [doi:10.7554/eLife.57443](https://doi.org/10.7554/eLife.57443)
4. Frémaux, N. & Gerstner, W. Neuromodulated spike-timing-dependent plasticity, and theory of three-factor learning rules. *Front. Neural Circuits* **9**, 85 (2016). [doi:10.3389/fncir.2015.00085](https://doi.org/10.3389/fncir.2015.00085)
5. Barrett, A. B. & Seth, A. K. Practical measures of integrated information for time-series data. *PLoS Comput. Biol.* **7**, e1001052 (2011). [doi:10.1371/journal.pcbi.1001052](https://doi.org/10.1371/journal.pcbi.1001052)
6. Tononi, G., Boly, M., Massimini, M. & Koch, C. Integrated information theory: from consciousness to its physical substrate. *Nat. Rev. Neurosci.* **17**, 450–461 (2016). [doi:10.1038/nrn.2016.44](https://doi.org/10.1038/nrn.2016.44)
7. Dayan, P. & Abbott, L. F. *Theoretical Neuroscience: Computational and Mathematical Modeling of Neural Systems*. MIT Press (2001).

<details>
<summary><b>Cite this profile</b></summary>

```bibtex
@misc{aris_profile,
  author       = {Aris},
  title        = {sa-aris: where software engineering meets computational neuroscience},
  year         = {2026},
  howpublished = {\url{https://github.com/sa-aris}},
  note         = {Living document; Figs. 3--5 regenerate every 12 hours}
}
```

</details>

<!-- ====================== FOOTER ====================== -->
<div align="center">
<sub>Every figure on this page is computed, not drawn — see <a href="https://github.com/sa-aris/sa-aris/tree/main/scripts"><code>scripts/</code></a>.</sub>
</div>
