from crewai import Crew
from app.agents.flashcard_agent import flashcard_agent, flashcard_task

mock_markdown = """
# Organic Chemistry Study Guide

Compiled notes from multiple sources on **Organic Chemistry** for exam prep.

---

## 1. Fundamentals of Organic Chemistry

### Structure and Bonding
- **Carbon Valency**: Carbon has 4 valence electrons, forming 4 covalent bonds.
- **Hybridization**:
  - sp³: Tetrahedral (109.5° bond angle).
  - sp²: Trigonal planar (120° bond angle).
  - sp: Linear (180° bond angle).
- **Electronegativity**: Influences bond polarity and reactivity.

### Resonance
- Molecules with conjugated systems can delocalize electrons.
- Example: Benzene has 6 π electrons spread evenly across the ring.

### Acid-Base Concepts
- **Bronsted-Lowry acid**: Proton donor.
- **Bronsted-Lowry base**: Proton acceptor.
- Organic acids often contain -COOH, while bases contain -NH₂ groups.

---

## 2. Functional Groups

### Alkanes
- Saturated hydrocarbons with single bonds.
- General formula: CₙH₂ₙ₊₂.
- Nonpolar, undergo combustion.

### Alkenes
- Unsaturated hydrocarbons with C=C double bonds.
- Undergo **electrophilic addition reactions**.
- Markovnikov’s rule: “The rich get richer” (H adds to carbon with more hydrogens).

### Alkynes
- Unsaturated hydrocarbons with C≡C triple bonds.
- Terminal alkynes are acidic (pKa ~25).

### Alcohols
- Contain -OH group.
- Classified as primary, secondary, or tertiary depending on carbon attachment.
- Can undergo oxidation:
  - 1° alcohol → aldehyde → carboxylic acid
  - 2° alcohol → ketone
  - 3° alcohol → resistant to oxidation

### Aldehydes and Ketones
- Both contain a carbonyl group (C=O).
- Aldehydes: Carbonyl at end of chain.
- Ketones: Carbonyl within chain.
- Reactivity: Nucleophilic addition (e.g., reduction to alcohols).

### Carboxylic Acids
- Contain -COOH.
- Strong hydrogen bonding, high boiling point.
- React with bases to form salts.

### Amines
- Derived from ammonia (NH₃).
- Classified as primary, secondary, tertiary.
- Basic due to lone pair on nitrogen.

### Aromatic Compounds
- Benzene and derivatives.
- Stabilized by resonance (aromaticity).
- Undergo **electrophilic aromatic substitution**:
  - Nitration
  - Halogenation
  - Sulfonation
  - Friedel-Crafts alkylation/acylation

---

## 3. Organic Reactions

### Substitution Reactions
- **SN1**:
  - Two-step (carbocation intermediate).
  - Rate depends only on substrate.
  - Favored in polar protic solvents.
- **SN2**:
  - One-step (backside attack).
  - Rate depends on both substrate and nucleophile.
  - Favored in polar aprotic solvents.

### Elimination Reactions
- **E1**: Two-step, carbocation intermediate.
- **E2**: One-step, strong base required.
- Zaitsev’s Rule: More substituted alkene is favored.

### Addition Reactions
- Alkenes and alkynes undergo addition of HX, X₂, H₂O, etc.
- Catalytic hydrogenation converts alkenes → alkanes.

### Oxidation and Reduction
- Oxidation: Increases bonds to oxygen or decreases bonds to hydrogen.
- Reduction: Increases bonds to hydrogen or decreases bonds to oxygen.
- Common reagents:
  - Oxidation: KMnO₄, CrO₃, PCC.
  - Reduction: LiAlH₄, NaBH₄, catalytic hydrogenation.

---

## 4. Spectroscopy and Structure Elucidation

### Infrared (IR) Spectroscopy
- Identifies functional groups by bond vibrations.
- Key peaks:
  - O-H stretch: broad, ~3300 cm⁻¹
  - C=O stretch: sharp, ~1700 cm⁻¹
  - C-H stretch: ~2900 cm⁻¹

### Nuclear Magnetic Resonance (NMR)
- **¹H NMR**:
  - Chemical shift depends on electron environment.
  - Integration shows number of protons.
  - Splitting follows n+1 rule.
- **¹³C NMR**:
  - Provides number of unique carbon environments.
  - Quaternary carbons appear weaker.

### Mass Spectrometry (MS)
- Measures molecular weight and fragmentation pattern.
- Base peak = most intense fragment.
- M⁺ peak = molecular ion.

---

## 5. Study Tips and Common Mistakes

- Don’t forget to consider resonance stabilization in carbocations.
- Watch out for **stereochemistry** in SN2 (always inversion of configuration).
- In elimination reactions, check if Hofmann product (less substituted) might be favored with bulky bases.
- IR peaks around 1700 cm⁻¹ almost always indicate a carbonyl.
- Practice drawing full mechanisms, not just products.

---

## End of Notes

"""

def run_flashcard_agent(markdown: str):
    crew = Crew(
        agents=[flashcard_agent],
        tasks=[flashcard_task]
    )
    return crew.kickoff(inputs={"markdown": markdown})

if __name__ == "__main__":
    flashcards = run_flashcard_agent(mock_markdown)
    print(flashcards)