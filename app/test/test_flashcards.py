from crewai import Crew
from app.agents.flashcard_agent import flashcard_agent, flashcard_task

mock_markdown = """
# Star Wars Study Guide

Compiled notes from multiple documents on **Star Wars** lore, characters, and technology.

---

## 1. Galactic History

### The Old Republic
- Existed thousands of years before the Galactic Empire.
- Constantly at war with the Sith.
- Known for Jedi-led armies and democratic institutions.

### The Clone Wars
- Conflict between the Galactic Republic and the Confederacy of Independent Systems (Separatists).
- Clones were created from bounty hunter Jango Fett.
- Led to the rise of Palpatine’s power.

### The Galactic Empire
- Founded by Sheev Palpatine after declaring himself Emperor.
- Dissolved the Republic Senate.
- Used fear, the Death Star, and Imperial military to maintain control.

### The Rebel Alliance
- A coalition of freedom fighters resisting the Empire.
- Leaders: Mon Mothma, Bail Organa, Princess Leia.
- Victory at the Battle of Yavin destroyed the first Death Star.

### The New Republic and the First Order
- New Republic replaced the Empire after the Battle of Endor.
- First Order emerged from remnants of the Imperial fleet.
- Resistance formed to oppose the First Order, led by Leia Organa.

---

## 2. The Force and Jedi Philosophy

### The Force
- An energy field created by all living things.
- Divided into the **Light Side** and **Dark Side**.
- Jedi follow the Light; Sith embrace the Dark.

### Jedi Order
- Guardians of peace and justice.
- Known for lightsabers, discipline, and selflessness.
- Famous Jedi: Yoda, Obi-Wan Kenobi, Anakin Skywalker, Luke Skywalker.

### Sith
- Dark Side users seeking power and domination.
- Rule of Two: a master and an apprentice.
- Famous Sith Lords: Darth Sidious (Palpatine), Darth Vader, Darth Maul.

### Prophecies
- The “Chosen One” would bring balance to the Force.
- Interpreted as Anakin Skywalker, though balance was debated.

---

## 3. Major Characters

### Luke Skywalker
- Farm boy from Tatooine, trained as a Jedi by Obi-Wan and Yoda.
- Destroyed the Death Star at Yavin.
- Redeemed his father, Anakin Skywalker.

### Darth Vader (Anakin Skywalker)
- Jedi Knight turned Sith Lord.
- Fell to the Dark Side under Palpatine’s influence.
- Ultimately sacrificed himself to destroy the Emperor and save Luke.

### Princess Leia Organa
- Senator, Rebel leader, and twin sister of Luke.
- Strong with the Force, later trained as a Jedi.
- Led the Resistance against the First Order.

### Han Solo
- Smuggler turned hero.
- Pilot of the Millennium Falcon.
- Partnered with Chewbacca, friend of Luke and Leia.

### Yoda
- Jedi Grand Master for centuries.
- Small in stature but incredibly powerful in the Force.
- Known for wisdom and cryptic speech patterns.

---

## 4. Technology and Starships

### Lightsabers
- Energy swords wielded by Jedi and Sith.
- Powered by kyber crystals.
- Colors often symbolize alignment: blue/green (Jedi), red (Sith).

### The Death Star
- Moon-sized space station and superweapon.
- Capable of destroying entire planets.
- Two were constructed; both destroyed by the Rebels.

### Millennium Falcon
- Corellian YT-1300 freighter modified by Han Solo.
- Known for speed, agility, and smuggling compartments.
- Made the Kessel Run in less than twelve parsecs.

### X-Wing Starfighter
- Primary starfighter of the Rebel Alliance.
- Known for versatility and proton torpedoes.
- Luke Skywalker flew an X-Wing in the Battle of Yavin.

### TIE Fighters
- Standard Imperial starfighters.
- No shields or hyperdrive; mass-produced.
- Recognized by their twin ion engines and screeching sound.

---

## 5. Key Battles

- **Battle of Yavin**: Rebels destroyed the first Death Star.
- **Battle of Hoth**: Imperial victory, Rebels evacuated the ice planet.
- **Battle of Endor**: Rebels destroyed the second Death Star, Palpatine defeated.
- **Battle of Starkiller Base**: Resistance destroyed the First Order’s superweapon.

---

## 6. Study Tips for Star Wars Trivia

- Remember the chronology: Republic → Empire → Rebellion → New Republic → First Order.
- The Rule of Two always applies to Sith: one master, one apprentice.
- Lightsaber colors often hint at allegiance, but not always.
- Many starships are named for animals (X-Wing, TIE Fighter, Star Destroyer).
- Family relationships drive much of the saga’s plot (Anakin → Luke & Leia → Ben Solo).

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