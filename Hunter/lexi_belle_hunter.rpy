label lexi_belle_hunter:
    $ selected_girl = current_event.participants[0]

    $ current_event.set_background("1.webp")

    player.character "After the pet training lessons, I can't find Lexi Belle anywhere."

    menu(title_text=f"I think The Hunter knows where she is."):
        "Need to contact a maniac.":
            pass

        "I'm tired of searching for lost girls.":
            $ current_event.end_event_early(reset_availability=True)
            return

    $ current_event.show_video("1_clothed.webm")
    pause

    "Hunter Assistant" "What's up, headmaster? Is someone missing again?"

    player.character "Where is Lexi Belle?"

    "Hunter Assistant" "Another freshly trained puppy ran away? Bad luck."

    player.character "I guess you know where Lexi is."

    "Hunter Assistant" "As always, the Live stream must be paid for first."

    menu(title_text=f"Pay for {selected_girl} training stream $100?"):
        "Pay from personal funds" if player.cash >= 100:
            player.character "I'll pay to 'The Hunter' maniac."
            $ player.modify_cash(-100)

        "I have so many girls at the Academy that I will not miss Lexi Belle.":
            selected_girl.character "Oh, no! Nobody can save me now."

            $ current_event.end_event_early(reset_availability=True)
            return

    $ current_event.show_video("6_bare-notop.webm")

    "The Hunter" "Look at our new pet girl."
    "The Hunter" "Did you really think, I wouldn't find and destroy that GPS tracker hidden in her clothes?"
    "The Hunter" "The poor girl didn't realize what dangerous game she'd gotten herself into."

    $ current_event.show_video("7_bare-notop,nobot.webm")

    "The Hunter" "Did you really planned to use a weak, silly girl against me?"
    "The Hunter" "Today she would learn what happens to undercover agents when they are uncovered."
    "The Hunter" "She will get harsh training, and that's only your fault."

    $ current_event.show_image("3_bare.webp")

    "The Hunter" "Heh! You thought that you could use Lexi to hunt... ME?"

    $ current_event.show_image("4_bare.webp")

    "The Hunter" "Poor girl was just a bait."

    $ current_event.show_image("5_bare.webp")

    "The Hunter" "She understood that after the GPS tracker was destroyed, nobody knew where she was."

    $ current_event.show_image("6_bare.webp")

    "The Hunter" "Anyway... you paid for the Live stream." 
    "The Hunter" "Let's see how our new pet is trained to live without hands."

    $ current_event.show_video("1_sex-give_oral.webm")
    pause

    $ current_event.show_video("2_sex-give_oral.webm")
    pause

    "The Hunter" "Real animals don't use hands, so perfect quadrober's hands must be restricted."

    $ current_event.show_image("1_bare.webp")

    player.character "Yes, I admit your victory. You're a true wildlife expert."
    player.character "But you're weak on modern technology."

    "The Hunter" "What are you talking about?"

    $ current_event.show_image("7_clothed.webp")

    player.character "Have you heard of RFID chips? Or maybe about remote-controlled buttplugs?"
    player.character "When you destroyed the GPS tracker, I was still receiving a signal from inside her ass."

    "The Hunter" "What the hell?!"

    $ current_event.show_image("8_clothed.webp")

    player.character "You were so courageous only because I was always so far away from you"
    player.character "Let's see — who is the hunter NOW!?"

    $ current_event.show_video("3_clothed.webm")
    pause

    $ current_event.show_image("9_clothed.webp")

    player.character "I also know that your assistant is preparing Lexi for the next client."
    player.character "That means you're alone in your hideout right now."
    player.character "Let's check how brave you are when I am getting closer."

    $ current_event.show_video("4_clothed.webm")
    pause

    $ current_event.show_image("10_clothed.webp")

    player.character "Damn it! Why did I warn him of my attack? He had time to react and ambush me."
    player.character "This Hollywood-style villain dialogue can bring me to the graveyard."

    $ current_event.show_image("11_clothed.webp")

    player.character "Hell! The bastard has disarmed me."

    $ current_event.show_video("5_clothed.webm")
    pause

    $ current_event.show_image("12_clothed.webp")

    player.character "Everything looks blurry after his punch."

    $ current_event.show_image("13_clothed.webp")

    player.character "He threw me to the floor. I gotta get up quickly."

    $ current_event.show_video("6_clothed.webm")
    pause

    $ current_event.show_image("14_clothed.webp")

    player.character "Pushed him off, but I gotta get out of the melee"
    player.character "Gotta keep my distance. Where's my gun and magazine?"

    $ current_event.show_video("7_clothed.webm")
    pause

    $ current_event.show_image("15_clothed.webp")

    player.character "Goodbye, The Hunter. You were cunning and strong, but fate is on my side."
    player.character "So tell me, Mr. maniac: who is the hunter now?!"

    $ current_event.show_image("16_clothed.webp")

    player.character "After The Hunter was down, I needed to find Lexi."

    $ current_event.show_video("5_bare.webm")
    pause

    player.character "She was prepared to serve the next client. That's not gonna happen."

    $ current_event.show_image("17_clothed.webp")

    player.character "Are you okay? I thought you'd be desperate and sad."

    selected_girl.character "Because he didn't pull out my buttplug, I knew you always knew where I was."

    $ current_event.show_image("18_clothed.webp")

    selected_girl.character "Wait, you just shot him in the head while he was moving?"

    player.character "Of course, I finished him with a headshot."
    player.character "I'm not a simple teacher here. I am the Headmaster."

    selected_girl.character "What about... Sasha Grey? What do we do with her?"

    $ current_event.show_image("_mods/girls/sasha_grey/photoshoots/Apprentice/14_revealing-notop.webp")
    pause

    player.character "Good question. She is having fun with a new girl right now."

    $ current_event.show_image("_mods/girls/sasha_grey/photoshoots/Apprentice/18_softcore-play_feet,notop.webp")
    pause

    player.character "She doesn't know about Hunter's death yet."

    $ current_event.show_image("_mods/girls/sasha_grey/photoshoots/Apprentice/15_softcore-play_feet,notop.webp")
    pause

    player.character "She definitely enjoys training pet girls."

    $ current_event.show_image("_mods/girls/sasha_grey/photoshoots/Apprentice/7_revealing-notop.webp")
    pause

    $ current_event.show_image("_mods/girls/sasha_grey/photoshoots/Apprentice/12_softcore-get_dildo_pussy,notop.webp")
    pause

    player.character "She likes to take advantage of captured girls."

    $ current_event.show_image("_mods/girls/sasha_grey/photoshoots/Apprentice/11_softcore-get_dildo_pussy,notop.webp")
    pause

    $ current_event.show_image("_mods/girls/sasha_grey/photoshoots/Apprentice/10_softcore-get_dildo_pussy,notop.webp")
    pause

    player.character "While under the influence of a maniac, she discovered the darker side of her personality."

    $ current_event.show_image("_mods/girls/sasha_grey/photoshoots/Apprentice/19_revealing-notop,nobot.webp")
    pause

    $ current_event.show_image("_mods/girls/sasha_grey/photoshoots/Apprentice/20_revealing-notop,nobot.webp")
    pause

    $ current_event.show_image("_mods/girls/sasha_grey/photoshoots/Apprentice/1_clothed.webp")
    pause

    player.character "But who is she now? When she's alone, without the influence of a maniac?"

    $ current_event.show_image("_mods/girls/sasha_grey/photoshoots/Apprentice/4_clothed.webp")
    pause

    player.character "We won't do anything to her now."

    $ current_event.show_image("_mods/girls/sasha_grey/photoshoots/Apprentice/2_clothed.webp")
    pause

    player.character "She must try to reclaim her identity"
    player.character "Will she heal herself, or will she emerge as a new Hunter?"

    $ current_event.show_image("_mods/girls/sasha_grey/photoshoots/Apprentice/3_clothed,cover.webp")
    pause

    player.character "She has to decide for herself who she really is."

    $ current_event.show_image("1.webp")

    player.character "With the Hunter death, there was no threat to my Academy anymore."
    player.character "I am the only one who can free-use my schoolgirl pets."

    return