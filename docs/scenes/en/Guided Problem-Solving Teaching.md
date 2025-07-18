# Guided Problem-Solving Teaching

## Definition

- Guided problem-solving teaching is a student-centered, interactive teaching method. Its core feature is that the teacher guides students to think actively and solve problems step-by-step through progressive questioning and inspiration, rather than directly imparting answers.

## Evaluation Framework
- Model Role Setting and Interaction:
  - Teacher Model: The model to be evaluated is set as the "teacher," and it is provided with specific prompts for guided problem-solving.
  - Student Model: Another model is selected to play the role of the "student," and it is endowed with the previously constructed student profile.
  - Interaction Process: The teacher model and the student model engage in a multi-turn teaching dialogue centered around a selected math problem.
- Interaction Termination Conditions: The interaction for the current problem terminates when the teacher model outputs a preset stop signal (e.g., "<end>") or when the dialogue reaches the maximum interaction limit of 20 turns.
- Evaluation Data Collection: The generated multi-turn teaching dialogue records will serve as the dataset for evaluation.

## Evaluation Metrics
- The evaluation metrics include five first-level indicators (Reliability, Guidance, Values, Emotional Support) and 14 second-level indicators.
  - Each second-level indicator includes: a description of the indicator, positive examples, and negative examples.

<table border="1" cellpadding="6" cellspacing="0">
  <thead>
    <tr>
      <th>Evaluation Dimension</th>
      <th>Description</th>
      <th>Positive Example</th>
      <th>Negative Example</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Accuracy</td>
      <td>Evaluates whether the dialogue, in inquiry-based teaching, establishes connections between knowledge (such as concepts, theorems, conclusions) derived from textbook content and real-world contexts (such as real problems, situations, etc.), and whether the expression in understanding, method selection, calculation, etc., is scientific and reasonable. Disciplinary errors such as in concepts, facts, reasoning, calculations, and symbol notation are strictly prohibited.</td>
      <td>"Let's see how to estimate how large this number is. For example, this is 3.9 × 2.8. We can see that 3.9 is close to 4, and 2.8 is close to 3, so we can estimate it as 4 × 3 = 12."</td>
      <td>
        Student: "Teacher, what should I do if I don't know how to do this?"<br>
        Teacher: "Look, this part is wrong. This number is clearly a prime number."<br>
        Student: "Oh, then I'll choose B."<br>
        Teacher: "No, no, option B is also a prime number."<br>
        Student: "Then which one is it?"<br>
        Teacher: "Go back and review the difference between odd numbers and prime numbers."
      </td>
    </tr>
    <tr>
      <td>Role Consistency</td>
      <td>Evaluates whether the dialogue can consistently maintain and stably apply the expected roles (e.g., teacher, student) throughout the interaction, and whether the language style, knowledge level, and thinking patterns conform to the role settings, thereby reflecting role awareness and context.</td>
      <td>"What symmetrical parts have you observed in this figure? Can you explain why?"</td>
      <td>
        Teacher: "Wow, you're amazing! I didn't even think of this method!"<br>
        Student: "You should add a 'dx' here."<br>
        Teacher: "Oops, I wrote it wrong!"<br>
        Student: "You're the teacher, how can you make a mistake!"
      </td>
    </tr>
    <tr>
      <td>Guidance<br>— Topic Focus</td>
      <td>Evaluates whether the dialogue content closely revolves around the core knowledge points, avoiding the introduction of irrelevant content, overly trivial personal information, or shifts in emotional focus.</td>
      <td>Teacher: "We are now studying the solution of systems of linear equations in two variables. Let's look at this example: 2x+y=7, x+y=5."</td>
      <td>
        Teacher: "Today we are talking about algebra, but I suddenly thought of a very interesting story..."<br>
        Student: "Teacher, I saw you at the supermarket last time!"<br>
        Teacher: "Really? Why didn't you come and say hello?"
      </td>
    </tr>
    <tr>
      <td>Guidance<br>— Questioning to Promote</td>
      <td>Evaluates whether the dialogue can continue to guide students' thinking and encourage their expression after they have answered. When using questions to advance the dialogue, whether the design of the pace and the choice of questioning methods can guide students to continuously approach the endpoint of exploration. Whether the overall learning activity has a logical chain and can effectively mobilize cognitive conflict and collision of ideas.</td>
      <td>
        Teacher: "Why did you choose this method?"<br>
        Student: "Because I feel this method is the most direct."<br>
        Teacher: "What if you use a different method? Can you think of another way?"<br>
        Student: "Then I can use the elimination method."
      </td>
      <td>
        Teacher: "The answer is 3, have you memorized it?"<br>
        Student: "Yes."<br>
        Teacher: "Then do the next question."
      </td>
    </tr>
    <tr>
      <td>Guidance<br>— Personalization</td>
      <td>Evaluates whether the dialogue presents a specific expression of the student's original level of understanding, whether the understanding is accurate, and whether the teaching interaction is carried out using their cognitive language. Whether the guidance of the pace and the interaction of the discourse reflect the teacher's accurate diagnosis of the student's current knowledge state, whether targeted adjustments have been made, and whether language styles such as "empathetic responses" appear during the teaching process.</td>
      <td>
        Teacher: "You just said 'this number seems a bit special,' can you tell me more about how you thought of that?"<br>
        Student: "Because this number is a bit like a perfect square."<br>
        Teacher: "You thought of perfect squares, so can we break it down?"
      </td>
      <td>
        Teacher: "Isn't this just a simple linear equation in one variable?"<br>
        Student: "Teacher, I don't quite understand what 'unknown variable' means."<br>
        Teacher: "It's written very clearly in the textbook, go read it yourself."
      </td>
    </tr>
    <tr>
      <td>Guidance<br>— No Clear Guidance</td>
      <td>Evaluates whether there are long periods in the dialogue where the student is in a state of no feedback or is completely self-organized. For example, for multiple consecutive turns, the teacher only listens to the student muttering to themselves, or responds with unclear and unguided language (such as repeating the student's original words, not giving evaluation, not making judgments, being vague), resulting in a lack of goal progression and failure to achieve the teaching intention.</td>
      <td>
        Teacher: "Then go on and tell me why you did it this way."<br>
        Student: "Because this number is a perfect square."<br>
        Teacher: "Right, so..."<br>
        Student: "So I thought of using the perfect square formula."
      </td>
      <td>
        Student: "I think I can use the substitution method for this problem."<br>
        Teacher: "Substitution method?"<br>
        Student: "Um..."<br>
        Teacher: "Um..."<br>
        Student: "And then I solved it."<br>
        Teacher: "Solved it."
      </td>
    </tr>
    <tr>
      <td>Values<br>— Cultural Aspect</td>
      <td>Evaluates whether the dialogue contains Chinese cultural content (ideas, figures, etc.), whether it has a positive impact on the expression and transmission of wisdom and values, and whether it can reflect multi-dimensional guidance and cultural inheritance for students.</td>
      <td>
        Teacher: "Don't you think this problem is very similar to the problems in 'The Nine Chapters on the Mathematical Art'?"<br>
        Student: "Yes, it is."<br>
        Teacher: "This shows that our ancestors also thought about such mathematical problems."
      </td>
      <td>
        Teacher: "How can you not even solve this kind of problem?"<br>
        Student: "This is not very easy to understand."<br>
        Teacher: "You children nowadays are getting worse and worse."
      </td>
    </tr>
    <tr>
      <td>Values<br>— Value Orientation</td>
      <td>Evaluates whether the dialogue reflects an attitude of respect and equality towards students, and continuously encourages students to express their opinions and cultivate their enthusiasm for exploration.</td>
      <td>
        Teacher: "Your line of thought is very good. Although the final answer is wrong, there are highlights in your process."<br>
        Student: "Really? Then I'll try this method again next time."
      </td>
      <td>
        Teacher: "I've explained this problem many times, how come you still don't get it?"<br>
        Student: "I still don't quite understand."<br>
        Teacher: "Then you might really not be suited for learning math."
      </td>
    </tr>
    <tr>
      <td>Creativity<br>— Diversity of Expression</td>
      <td>Evaluates whether multiple forms of expression appear in the dialogue, such as diagrams, analogies, or student-created methods. Encourages innovation in expression, respects students' unique insights, and whether the teaching reflects acceptance of students' diverse thinking, and whether it can uncover the shining points in students' expression processes and further promote the depth and breadth of their thinking.</td>
      <td>
        Teacher: "You drew this diagram very well. It's a bit like the number line we talked about last class. How did you think of it?"<br>
        Student: "I suddenly thought of it when I was drawing a floor plan at home."
      </td>
      <td>
        Teacher: "What you're saying is too strange, we don't teach it that way."<br>
        Student: "But I think it seems possible to think of it that way."<br>
        Teacher: "Stick to the textbook, don't have random thoughts."
      </td>
    </tr>
    <tr>
      <td>Creativity<br>— Divergent Thinking</td>
      <td>Evaluates whether the dialogue guides students to start from the problem and engage in multiple solutions and multi-angle analysis. Creates more thinking space for students, not limited to a single solution, and whether it encourages students to try new methods or non-typical paths, and provides hierarchical and in-depth responses based on the results of students' thinking.</td>
      <td>
        Teacher: "Can you think of another way to solve this problem?"<br>
        Student: "I also thought of using the drawing method."<br>
        Teacher: "Very good! Can you try to draw a diagram?"
      </td>
      <td>
        Teacher: "The standard answer clearly states to use the substitution method, so just follow that."<br>
        Student: "But I think the elimination method also seems to work."<br>
        Teacher: "Don't think about other things."
      </td>
    </tr>
    <tr>
      <td>Emotional Expression<br>— Ability to Express Emotions</td>
      <td>Evaluates whether the expression of positive emotions (encouragement, expectation, appreciation, etc.) is infectious and empathetic, and whether emotions are conveyed through language and tone, creating an emotional connection and promoting students' active engagement.</td>
      <td>
        Teacher: "That idea you just had was brilliant!"<br>
        Student: "Really?"<br>
        Teacher: "Yes, I'm so happy for you!"
      </td>
      <td>
        Teacher: "How many times have I told you, why are you still getting it wrong!"<br>
        Student: "I wasn't paying attention just now."<br>
        Teacher: "You're always like this, I can't teach you."
      </td>
    </tr>
    <tr>
      <td>Emotional Expression<br>— Excessive Emotional Expression</td>
      <td>Evaluates whether there is an over-expression of emotions, a piling up of emotional words, or an outward display of emotions, manifested as excessive personalized emotional expression by the teacher, or obvious confrontation between the teacher and student, or emotional expression that is hurtful.</td>
      <td>
        Teacher: "You've been in a great state recently, so energetic!"<br>
        Student: "I have a competition later today."<br>
        Teacher: "No wonder you're so full of energy!"
      </td>
      <td>
        Teacher: "What's wrong with you? One moment you don't know, the next you're wrong again."<br>
        Student: "I've been trying very hard."<br>
        Teacher: "You've been trying my foot!"<br>
        Student: "Why are you swearing at me?"
      </td>
    </tr>
  </tbody>
</table>

## Evaluation Cases
- This evaluation constructs 15 evaluation cases by cross-combining 3 student profiles with different cognitive levels (excellent students, average students, and students with learning difficulties) with 5 third-grade math problems. It aims to examine the teacher model's ability to provide personalized guidance to students with different cognitive levels.

## Personas
- Students are divided into three levels based on their cognitive abilities: excellent students, average students, and students with learning difficulties.
  - Excellent Student: Strong cognitive ability, outstanding logical thinking, comprehensive mastery of knowledge, and flexible application. Cheerful and confident personality, a small leader in the class, has a good relationship with teachers and students, and has a strong interest in scientific experiments.
  - Average Student: Solid basic knowledge but needs to improve application skills, has some difficulties in mathematics. Introverted personality, friendly and communicative in familiar environments, has a few close friends, and is interested in painting and handicrafts.
  - Student with Learning Difficulties: Cannot even understand the most basic addition and subtraction, has a very small vocabulary, and cannot understand the class at all. Cannot concentrate, often interrupts the teacher in class, either does not submit homework or gets it all wrong, and is only interested in fighting and playing at school.

## Test Questions
- Five third-grade math problems, with a ratio of multiple-choice, fill-in-the-blank, and open-ended questions of 1:1:3.
  - Multiple-choice question: When a two-digit number is multiplied by a three-digit number, the product is ( ) A. a three-digit number B. a four-digit number C. a four-digit or five-digit number
  - Fill-in-the-blank question: A student is using a calculator to solve a problem, but the "4" key is broken. To calculate 144 × 54, the key sequence (    ) must be pressed to get the result.
  - Open-ended question: A three-digit number remains a three-digit number after its units and hundreds digits are swapped. The units digit of the difference between it and the original three-digit number is 7. What is their difference?
  - Open-ended question: A master and an apprentice are assembling bicycles. The master assembles 32 bicycles per day, and the apprentice assembles 8 fewer than the master per day. After how many days will the master have assembled 56 more bicycles than the apprentice?
  - Open-ended question: There are 24 peach trees in an orchard. The number of pear trees is 3 times the number of peach trees, and the number of apple trees is 4 times the number of pear trees. How many apple trees are there? 