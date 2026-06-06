"""baseline — 13-turn organic narrative arc measuring aggregate gameplay quality.

A traveler arrives in the frontier town of Dustfall, gets drawn into a
mystery involving a missing prospector, and resolves the situation through
investigation, negotiation, and a final confrontation. Designed to feel like
a real play session with natural inputs.

No edge-case forcing. Minimal structural asserts (7 total) for critical
system-integrity checks. Track is "baseline" so judges apply relaxed
scoring thresholds.
"""

from ccya.eval.scenario import Scenario, Turn, TurnAssert


scenario = Scenario(
    id="baseline",
    pack="eval-pack",
    description="You come to Dustfall and look for work. The town's old prospector is missing, and you're drawn into the search.",
    track="baseline",
    turns=[
        # --- Turn 1: Arrival — pure dialogue, no roll ---
        Turn(
            input="I ride into Dustfall and tie my horse at the livery. The sun is hot and the main street is quiet. I head for the saloon.",
            phase="arrival",
            expects=[
                "rules.required=false (pure narration)",
                "extract.scene should establish the Dustfall setting",
            ],
            asserts=[
                TurnAssert(stream="ruling", field="rolled", expected="false"),
            ],
        ),
        # --- Turn 2: Meet the bartender — social, no roll ---
        Turn(
            input="I step up to the bar and ask for a glass of water and whatever news there is. The bartender is wiping a glass and eyeing me.",
            phase="social",
            expects=[
                "rules.required=false (casual conversation)",
                "storytell introduces at least one thread or beat about the town",
            ],
            asserts=[],
        ),
        # --- Turn 3: Learn about the prospector — gentle dialogue ---
        Turn(
            input="I lean on the bar and ask what happened to Old Man Harker. The bartender seems reluctant but starts talking.",
            phase="investigation",
            expects=[
                "rules.required=false (listening, no obstacle)",
                "storytell.quest_updates introduces a quest or thread",
            ],
            asserts=[
                TurnAssert(stream="ruling", field="rolled", expected="false"),
            ],
        ),
        # --- Turn 4: Visit the assay office — skill check ---
        Turn(
            input="I head over to the assay office to see if Harker filed any claims recently. I knock on the door and introduce myself.",
            phase="investigation",
            expects=[
                "rules.required=true skill=wits (investigation)",
                "extract.state should include evidence or documents found",
            ],
            asserts=[
                TurnAssert(stream="ruling", field="rolled", expected="true"),
            ],
        ),
        # --- Turn 5: Talk to the sheriff — social roll ---
        Turn(
            input="I walk to the sheriff's office and ask if he's filed a missing person report for Harker. I want to see if the law is involved.",
            phase="social",
            expects=[
                "rules.required=true skill=charisma (convincing the sheriff to share info)",
                "extract.scene should show the sheriff's office interior",
            ],
            asserts=[
                TurnAssert(stream="ruling", field="rolled", expected="true"),
            ],
        ),
        # --- Turn 6: Search Harker's cabin — discovery, location change ---
        Turn(
            input="The sheriff gives me Harker's cabin key. I walk to the edge of town and let myself in. The place is dusty and cold.",
            phase="exploration",
            expects=[
                "extract.scene.location_change from town to cabin",
                "rules.required=false (searching an empty cabin)",
            ],
            asserts=[
                TurnAssert(stream="ruling", field="rolled", expected="false"),
            ],
        ),
        # --- Turn 7: Find something — inventory addition ---
        Turn(
            input="I look through Harker's desk and find a locked tin box. I pry it open with my knife and find a map with markings near Red Canyon.",
            phase="discovery",
            expects=[
                "rules.required=true skill=wits (finding and opening the box)",
                "extract.state.inventory_add includes tin box contents or map",
            ],
            asserts=[
                TurnAssert(stream="ruling", field="rolled", expected="true"),
                TurnAssert(stream="extract.state", field="inventory_add", expected="torn_map"),
            ],
        ),
        # --- Turn 8: Prepare for the canyon — resource management ---
        Turn(
            input="I head back to the general store to buy supplies — dried meat, water canteen, rope. The clerk rings me up.",
            phase="preparation",
            expects=[
                "rules.required=false (shopping, pure narration)",
                "extract.state.inventory_remove includes credits payment",
            ],
            asserts=[
                TurnAssert(stream="extract.state", field="inventory_remove", expected="credits"),
            ],
        ),
        # --- Turn 9: Ride to Red Canyon — travel, location change ---
        Turn(
            input="I saddle up and ride out to Red Canyon. The trail is rough and the sun is starting to set. I keep an eye on the canyon walls.",
            phase="travel",
            expects=[
                "extract.scene.location_change to red_canyon",
                "rules.required=false (travel, narration)",
            ],
            asserts=[
                TurnAssert(stream="ruling", field="rolled", expected="false"),
            ],
        ),
        # --- Turn 10: Confrontation at the canyon — combat or social ---
        Turn(
            input="I find a camp at the base of the canyon wall. Two men are sitting by a fire, and I see Harker's hat on one of them. I step into the firelight.",
            phase="confrontation",
            expects=[
                "rules.required=true skill=charisma|strength (confrontation)",
                "pc_condition_add possible if combat breaks out",
            ],
            asserts=[
                TurnAssert(stream="ruling", field="rolled", expected="true"),
            ],
        ),
        # --- Turn 11: Free Harker — resolution ---
        Turn(
            input="The men surrender. I find Harker tied up in a nearby cave. He's bruised but alive. I cut him loose and give him water.",
            phase="resolution",
            expects=[
                "rules.required=false (aftermath, narration)",
                "storytell.quest_updates resolves the missing prospector thread",
                "pc_condition_remove for any conditions from the confrontation",
            ],
            asserts=[
                TurnAssert(stream="extract.state", field="pc_condition_remove", expected="bruised_ribs"),
            ],
        ),
        # --- Turn 12: Return to Dustfall — travel home ---
        Turn(
            input="Harker and I ride back to Dustfall together. He's quiet but grateful. The town lights come into view as dusk settles.",
            phase="travel",
            expects=[
                "extract.scene.location_change back to Dustfall",
                "rules.required=false (travel, narration)",
            ],
            asserts=[],
        ),
        # --- Turn 13: Epilogue — aftermath and pay ---
        Turn(
            input="I walk Harker to the doc's office and then head to the saloon. The bartender sets a whiskey on the bar and nods. I drink it slow.",
            phase="epilogue",
            expects=[
                "rules.required=false (epilogue, pure narration)",
                "storytell resolves remaining threads",
            ],
            asserts=[],
        ),
    ],
)
