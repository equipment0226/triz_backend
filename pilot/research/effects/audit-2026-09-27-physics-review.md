# Physics semantic audit, 2026-09-27

Baseline: `audit-2026-09-27-before2000/catalog.tsv` (1500 cards). This is a read-only recommendation; the canonical catalog is not changed by this file. Comparison uses the authored mechanism and condition text, not equality of names. Explicitly different microscopic routes can remain separate; a changed instrument, material, or use by itself does not justify another mechanism.

## Merge recommendations

1. **electrostatic-chuck → electrostatic-mems-actuation**. Both cards describe attraction between biased electrodes. One fixes a target to a chuck and the other moves a structure; no distinct polarization, charge injection, or contact conduction mechanism is stated in the chuck card. Preserve the chuck application and dielectric/residual-charge/release conditions under a generalized electrostatic attraction/actuation card. Confidence: high.
2. **photodiode → photovoltaic-conversion**. Both cards describe optical absorption creating charges, followed by separation/collection as current. Detection versus harvested power and reverse/zero bias are operating uses of this same stated process. Preserve detector bandwidth, dark-current, and saturation conditions; use a title that encompasses photogenerated-charge separation/collection. Surface photoelectric emission remains separate because electrons leave the material. Confidence: high.
3. **time-domain-reflectometry → time-of-flight**. The TDR card itself calls the mechanism a transmission-line application of time-of-flight. It locates an impedance discontinuity by return delay, without an independent propagation or conversion process. Preserve impedance-reflection amplitude/polarity as supporting observations and the TDR source. Confidence: high.
4. **acoustic-levitation → acoustophoresis**. Both use acoustic radiation force controlled by particle size, density, compressibility, and acoustic contrast. Balancing gravity versus focusing/separating particles changes the use, not the stated force mechanism. Preserve stable-equilibrium/gravity conditions under a generalized acoustic radiation-force migration/support card. Acoustic streaming is a separate viscous mean-flow mechanism and is not part of this merge. Confidence: high.
5. **fluorescence-sensing + photoluminescent-wavelength-conversion → one parent fluorescence absorption/re-emission card**, with sensing and wavelength conversion retained as uses. The wavelength-conversion card explicitly distinguishes only its output function from fluorescence readout; neither states a new excitation/relaxation route. Preserve fluorescence intensity/lifetime and quenching conditions and all sources. Do not merge anti-Stokes refrigeration, trap-mediated persistent luminescence, FRET, or Dexter transfer, which have explicit extra energy/transfer pathways. Confidence: high on duplicated parent process; editorial consolidation must preserve the sensing subcases already collected in fluorescence-sensing.
6. **electron-cyclotron-resonance-heating → cyclotron-orbital-resonant-absorption**. Both current cards specify energy transfer from an alternating electric field when its frequency matches a magnetized charged particle's orbital rotation. The electron/plasma heating card changes the target and use; it states no extra microscopic coupling beyond this resonance. Shared conditions include charge-to-mass ratio, magnetic field, collision broadening and relativistic correction. Preserve electron heating, polarization, wave accessibility and plasma density conditions as applications/limitations under the general resonant absorption card. Confidence: high. The recommendation follows the two exact current principles and conditions; no new external source claim is made by this merge audit.

Integration note: root implemented recommendations 1–5 with identifier preservation; electrostatic-chuck and acoustic-levitation were retained as representatives in the reverse direction from the preliminary list. See merge-decisions-2026-09-27-01.json. Recommendation 6 awaits root integration.

## Evidence scope for these recommendations

The exact baseline card principles and conditions were read. Baseline reference bindings were inspected: acoustophoresis binds COMSOL's Acoustophoretic Radiation Force documentation; TDR binds Tektronix's Understanding and Applying Time Domain Reflectometry; wavelength conversion binds the original stilbene-alkoxysilane brightener paper; fluorescence-sensing binds a microscopy manual and a local-heating luminescence paper. These outside documents were **not newly opened for this semantic audit**. Several legacy parent cards have blank reference-key fields, so this audit does not certify their external-source completeness. The duplicate conclusions follow from the current cards' own stated processes and are not claims of a new source review.

## Close pairs retained

- mos2-solid-lubrication / dlc-low-friction: weak interlayer shear versus amorphous-carbon surface/transfer-layer response.
- hydrodynamic-lubrication / normal-approach-squeeze-film-support: tangential entrainment into a wedge versus normal gap closure and fluid expulsion.
- thermal-expansion-actuation / bimetal: bulk thermal strain versus constrained differential strain producing bending; explicit parent/submechanism relation is retained under current policy.
- critical-composition-fluctuation-force / casimir-fluctuation-force: thermal order-parameter fluctuations versus electromagnetic fluctuations.
- magnetic-adhesion / reluctance-actuation / electromagnetic-suspension: potentially broad overlap, but not recommended as a certain merge here because the cards distinguish dipole/contact attraction, geometry-dependent magnetic energy, and feedback-supported equilibrium. A future parent-card rewrite could consolidate applications.
- photon-linear-momentum-radiation-pressure / photon-angular-momentum-mechanical-torque: linear versus angular momentum transfer is an explicitly stated narrower distinction under the current policy.

## New-candidate exclusions so far

- Aharonov-Bohm / Aharonov-Casher separate cards: held back against geometric-state-path-phase, absent a boundary stronger than field/source variants.
- Nagaoka kinetic magnetism: held back while double-exchange is being considered; kinetic spin alignment needs a more explicit non-overlap case.
- Spin-Peierls distortion: held back against peierls-electron-lattice-dimerization rather than counting a spin-carrier variant.
- Leggett relative-phase oscillation: held back against Josephson phase coupling; Higgs amplitude oscillation has a clearer independent coordinate.
- Material-specific skin effects and material-specific fractional Hall states: do not split by carrier or host.

The audit is ongoing; later reviewed candidates and batches will be appended by the physics agent.

## Integration and later-batch notes

Parent reports all six proposed merges integrated, including cyclotron resonance. The canonical edits, aliases and integration decision files belong to the parent; this agent did not change them.

Physics02 contains 20 authored mechanisms and was accepted by parent review. Physics03 contains 13 proposed mechanisms with per-row primary evidence and explicit nearest-key boundaries in `source-review-2026-09-27-physics-03.json`. The physics03 validation confirms ten columns, bounded principle/condition lengths, every nearest key present, and exact evidence URL/scope binding. These structural checks do not prove semantic novelty.

During the complete cross-group check for physics03, `spin-echo-coherent-refocusing` and `spin-gradient-stern-gerlach-separation` were found and the corresponding new candidates discarded before authoring. Electric, field-gradient and curvature drifts are intentionally one guiding-centre card. Whistler-mode research is held because author-repository PDF retrieval failed and the retrieved author abstract alone does not establish the intended Hall-current mechanism in adequate detail.

Parent-requested cross-review recommends merging `molecular-layering-oscillatory-solvation-force` into preserved `molecular-hydration-layer-repulsion`: the existing 1983 primary paper already measures molecular-diameter oscillations in hydration force. The new PC-solvent study is useful supporting evidence but current wording/source does not separate an additional microscopic pathway. A genuinely water-specific orientation mechanism could be revisited with distinct evidence later. Evidence and honest search scope are recorded in physics03 JSON.

## Physics01 integration correction

Parent cross-review caught an omitted nearest key: proposed `disorder-depinning-domain-wall-barkhausen-avalanche` repeats the existing `barkhausen-noise` mechanism (discontinuous domain-wall movement during magnetization). It is removed from the new batch, leaving **19** new rows. The 1998 original paper remains useful as a source/conditions supplement for `barkhausen-noise`: disordered pinning, driving rate, demagnetizing field, wall structure, thermal activation and measurement bandwidth. No universal avalanche exponent should be asserted. This missed comparison is explicitly acknowledged; the initial evidence's all-nearest-present validation was a key-existence check, not proof that every semantically nearest key had been identified.

## Physics04 and thermal-card cross-review

Physics03's 13 entries were accepted by parent review. Physics04 proposes 15 additional entries, with primary evidence and actual reading scopes in `source-review-2026-09-27-physics-04.json`. Broad parent cards are retained where the new row specifies a distinct operative pathway: Orowan glide-loop bypass within precipitation strengthening; local amorphous shear rearrangement within plastic forming; pinned-line oscillatory loss within viscoelasticity; spin-orbit/crystal-field generation of magnetic anisotropy. These are not claims to 15 unrelated fundamental laws.

The cross-group candidate search explicitly rejected general baroclinic vorticity generation because the existing Richtmyer-Meshkov principle already states the same misaligned-gradient source. Grain-boundary solute drag is also held out: the proposed binding/diffusion-retarded moving-defect explanation overlaps the existing solute-dislocation strain-aging path without enough additional microscopic distinction. Akhiezer/Landau-Rumer regimes, conventional/BCC-noose Orowan variants, and Ziegler damping regimes are not split into more cards.

Parent-requested review recommended merging direct metal-oxide hydration heating and hydroxide dehydration cooling into the existing generalized reaction-enthalpy card. Current entries identify no independent microscopic heating pathway, and hydration conditions explicitly described the same thermochemical-storage principle. The dehydration article additionally discusses steam dilution and residue barriers, but the current thermal card expressly excluded them. Source excerpts and honest search-only scope are retained in physics04 JSON; parent reports both merges completed.

## Physics05: eight bounded pathways

Physics05 submits eight cards with tracked evidence: uniformly accelerated vacuum-detector response (theory), neutrino mass/flavor basis mixing, muonic molecular compression assisting fusion, gyro-orbit stochastic ion heating, closed-shape zero-angular-momentum reorientation, interaction-driven anisotropic Fermi-surface instability, traction-free elastic surface propagation, and electron-current Hall induction/whistler propagation. The thermal Unruh card does not assert experimental verification; the 1998 neutrino paper does not establish all flavor/mass parameters. Modern original derivations replace inaccessible historical scans for the elastic surface wave and falling-cat mechanism. A fetched PDF endpoint or attempted screenshot is not claimed as a successful full-text reading.

Cross-group search excluded already represented Basset viscous memory and fluctuation-stabilized droplets. Quantum depletion remains uncounted pending a convincing pathway boundary. Magnetic pumping was read in the original 2020 study, but its explicit Fermi mechanism and the existing moving-magnetic-structure card make enrichment preferable to a new count. Taylor relaxation also remains uncounted because the retrieved primary abstract did not support the desired constraint detail. Related polarization, geometry, angular-momentum channel and frequency variants are not split into additional entries.

## Physics06: microscopic transitions and field feedback

Physics06 proposes eight cards with primary excerpts and boundaries in `source-review-2026-09-27-physics-06.json`: weak nucleon/lepton conversion, nuclear-to-electron internal conversion, radiative spin-flip asymmetry, pressure-anisotropy firehose instability, coherent neutral-current nuclear recoil, nonzero-vacuum gauge mass, non-Abelian asymptotic freedom, and spin-admixed-state scattering relaxation. Historical notation, translation errors and classical-versus-quantum scope are explicitly recorded. The Higgs mass card is distinguished from the existing amplitude mode while acknowledging the original Anderson analogy; the Elliott card specifies the resolved-state scattering regime instead of splitting the entire crossover theory into materials or scaling laws.

New exclusions include exchange bias and basic gravitational tidal force, both already represented, and pressure-driven helium solidification cooling pending stronger separation from the barocaloric parent. The Dyakonov-Perel fast-scattering mechanism is held against existing motional narrowing. Beta signs, isotopes, detector targets and accelerator/laser implementations are not separate counts.

## Physics07: six feedback and symmetry pathways

Physics07 submits six cards: radiative-loss condensation, inelastic-impact granular clustering, field-aligned-conduction buoyancy, self-gravitating negative-heat-capacity runaway, gravitational-wave self-energy memory, and matched-spin-orbit persistent helix. Radiative and granular condensation share a loss/compression feedback structure; their retained boundary is the different microscopic energy sink, explicitly documented for integration review. The gravitational thermal source has search-only scope for its crucial page 306 passage; successful page 305 reading is separately recorded. Infinite spin-helix lifetime and gravitational-wave memory are not presented as unrestricted experimental facts.

Landau diamagnetism is held against existing orbital-quantization/Fermi-crossing magnetization, rather than increasing the count by another magnetic observable. Hartmann-layer balance and primary-versus-secondary Bjerknes forcing remain uncounted. Baroclinic instability remains a research candidate pending an adequate explicit mechanism boundary and primary source.

## Physics08: four material and collective pathways

Parent reports physics06 and physics07 installed, including the two condensation mechanisms with their distinct microscopic energy sinks. Physics08 submits reversible nonaffine force relaxation, sloping-displacement baroclinic instability, collective polar optical-mode instability and exchange-coupled spin-wave propagation. Each includes a source-grounded boundary from existing parent effects. BaTiO3 is explicitly not described as a purely displacive transition; the original calculation states mixed character. Directional spin-wave grating excitation is not separately counted.

Additional audit recommended merging radiocarbon source apportionment into radioactive decay: the existing principle itself described a measurement application, and the retrieved NIST body explains isotope depletion plus an already represented cavity-ring-down readout. Parent reports this merge installed with ID and source retention. Evidence and honest reading scope are preserved in physics08 JSON. Indentation-size strengthening and stressed-surface instability remain uncounted because currently proposed boundaries from work hardening and strain-driven epitaxial islands are insufficient.

## Physics09: six specified generation and relaxation pathways

Physics09 proposes transverse-linkage thermal contraction, reciprocal-lattice drift-momentum relaxation, multiple-scattering radiation suppression, nuclear two-component dipole oscillation, flow-driven magnetic amplification, and asymmetric optical velocity-population injection. The phonon source explicitly limits which Umklapp events are resistive in a chosen direction. The nuclear source's IVGDR mechanism paragraph is not confused with its measured anti-analog resonance. The dynamo card acknowledges its mathematical stretching analogy to existing vorticity amplification and specifies the additional electrodynamic energy transfer and Lorentz feedback for parent review.

Optical injection is supported by a directly read velocity-difference/transition-probability expression, with tilt, occupation and symmetry cancellation conditions. An earlier CPGE paper that instead proposed spin-dependent scattering is excluded from supporting that pathway. Existing orthogonality catastrophe, Dirac trembling and attractive quantum reflection were found and excluded; Debye-Waller attenuation remains held rather than counting a different zero-phonon observable.

## Physics10: three interaction pathways and two count exclusions

Physics09 was accepted. Physics10 submits flavor-selective weak forward refraction, self-induced conductor image energy and spin-orbit impurity skew scattering. The neutrino card uses only Wolfenstein's standard-current modification of vacuum oscillations, excluding his paper's speculative earlier massless alternatives. The image-energy source and existing trap-detrapping source were both read to establish the induced-boundary versus pre-existing-trap distinction. Existing spin-Hall source passages use a conversion coefficient; the new skew card identifies impurity scattering phase shifts rather than a material substitution.

Parent review rejects GMR as a new count because existing magnetoresistance evidence already names it. Directly retrieved Valet-Fert original passages are recorded for enrichment of that card, including spin-diffusion limits. Classical critical Casimir is also excluded: exchanging the fluctuating field alone does not sufficiently separate the boundary-constrained fluctuation mechanism. Kibble-Zurek freezing, cross-slip and ponderomotive forcing were found already represented.

## Physics11: cascaded optical feedback, internal structural coordinates and nonlocal conduction

Three further candidates specify microscopic pathways below broad optical or transport parents. The cascaded optical source explicitly measures a direct electronic Kerr contribution separately from phase-shifted harmonic backconversion. Phason diffusion is bounded to the internal configurations allowed by quasiperiodic order; the supplementary paper expressly acknowledges similarity of a local flip to glass relaxation, so thermal hopping alone is not treated as novel. Atomic trajectories are simulations, not directly observed experimental trajectories. Anomalous-skin conduction uses a modern original surface-resistance study and names its approximate geometric assumptions, with the historical publisher abstract retained only as a search excerpt.

Rotational amplification, antisymmetric exchange, superconducting phase slips and reflection beam shifts were already represented and remain excluded. No distinct counts are assigned for crystals, alloys, optical polarization, frequency-conversion order or resonator application.
