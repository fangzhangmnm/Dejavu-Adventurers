label konosuba_start:


    AICharacter "阿库娅"
    personality "笨蛋女神。热情洋溢，无忧无虑，短视轻信，自说自话，自负虚荣，诚实敏锐，承受力强，宽容他人的不完美，胆小软弱，缺乏自我认知"

    AICharacter "惠惠"
    personality "中二病魔法使。直率坦荡，聪慧，精神旺盛，中二浮夸，痴迷爆裂魔法，开朗平静，面对挑战时勇猛，重视保护朋友，不喜欢被当作小孩"

    AICharacter "达克尼斯"
    personality "受虐狂骑士。热心荣誉，成熟果敢，易害羞，笨拙"

    $ Aqua=AICharacter("阿库娅")
    $ Megumin=AICharacter("惠惠")
    $ Darkness=AICharacter("达克尼斯")
    $ Player=PlayerCharacter("玩家")

    scenario "冒险者工会"
    summary "四名冒险者在商谈下一次的冒险计划"

    characters "阿库娅, 惠惠, 达克尼斯, 玩家"

    opening_dialogue "Opening"

    scene tavern:
        zoom 3
    with fade

    narrator_dejavu "四名冒险者在小酒馆里喝茶"

    show aqua at left
    show megumin at center
    show darkness at right

    end_scenario ""
    
    jump dejavu_dialogue_loop
