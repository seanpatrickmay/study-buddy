from crewai import Crew
from app.agents.tav_agent import extraction_agent, extraction_task, verification_agent, verification_task
from app.utils.tavily_handler import attach_tools_to_agent
from app.utils.tavily_handler import create_tavily_tools
from crewai import Task

# Machine Learning markdown content for testing
mock_markdown = """
# Machine Learning Fundamentals

A comprehensive guide to understanding **Machine Learning** concepts and algorithms.

---

## 1. Introduction to Machine Learning

### What is Machine Learning?
- **Machine Learning**: A subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed.
- **Algorithm**: A set of rules or instructions given to an AI system to help it learn on its own.
- **Training Data**: The initial dataset used to train machine learning models.

### Types of Learning
- **Supervised Learning**: The algorithm learns from labeled training data.
- **Unsupervised Learning**: The algorithm finds patterns in unlabeled data.
- **Reinforcement Learning**: The algorithm learns through trial and error with rewards and penalties.

---

## 2. Core Concepts

### Neural Networks
- **Neuron**: Basic unit of a neural network that receives inputs and produces an output.
- **Layer**: Collection of neurons operating together at a specific depth within a neural network.
- **Activation Function**: Mathematical equation that determines the output of a neural network.
- **Backpropagation**: Algorithm for training neural networks by calculating gradients.

### Model Training
- **Epoch**: One complete pass through the entire training dataset.
- **Batch Size**: Number of training examples utilized in one iteration.
- **Learning Rate**: A hyperparameter that controls how much to change the model in response to error.
- **Gradient Descent**: Optimization algorithm to minimize the cost function.

### Evaluation Metrics
- **Accuracy**: The ratio of correctly predicted observations to total observations.
- **Precision**: The ratio of correctly predicted positive observations to total predicted positive observations.
- **Recall**: The ratio of correctly predicted positive observations to all observations in actual class.
- **F1 Score**: The weighted average of Precision and Recall.

---

## 3. Common Algorithms

### Linear Regression
- Predicts a continuous target variable based on linear relationships.
- Uses least squares method to minimize error.
- Equation: y = mx + b

### Decision Trees
- Tree-like model of decisions and their possible consequences.
- Uses information gain or Gini impurity for splitting.
- Can handle both numerical and categorical data.

### Support Vector Machines (SVM)
- Finds the hyperplane that best separates classes.
- Effective in high-dimensional spaces.
- Uses kernel trick for non-linear classification.

### K-Means Clustering
- Unsupervised algorithm that groups data into K clusters.
- Minimizes within-cluster sum of squares.
- Requires specifying number of clusters beforehand.

---

## 4. Deep Learning

### Convolutional Neural Networks (CNN)
- **Convolution**: Mathematical operation that applies filters to input data.
- **Pooling**: Downsampling operation to reduce spatial dimensions.
- **Feature Map**: Output of applying filters to input image.
- Primarily used for image recognition and processing.

### Recurrent Neural Networks (RNN)
- **Hidden State**: Memory that captures information about previous inputs.
- **LSTM**: Long Short-Term Memory networks that can learn long-term dependencies.
- **GRU**: Gated Recurrent Units, simplified version of LSTM.
- Used for sequential data like text and time series.

### Transformers
- **Attention Mechanism**: Allows model to focus on different parts of input sequence.
- **Self-Attention**: Attention applied to the same sequence.
- **Positional Encoding**: Adds position information to input embeddings.
- Foundation for modern NLP models like BERT and GPT.

---

## 5. Practical Considerations

### Overfitting and Underfitting
- **Overfitting**: Model performs well on training data but poorly on new data.
- **Underfitting**: Model is too simple to capture underlying patterns.
- **Regularization**: Technique to prevent overfitting (L1, L2, Dropout).
- **Cross-Validation**: Method to assess model generalization.

### Feature Engineering
- Process of creating new features from existing data.
- **Normalization**: Scaling features to a standard range.
- **One-Hot Encoding**: Converting categorical variables to binary vectors.
- **Feature Selection**: Choosing most relevant features for the model.

### Deployment Considerations
- **Model Versioning**: Tracking different versions of trained models.
- **A/B Testing**: Comparing performance of different models in production.
- **Model Monitoring**: Tracking model performance over time.
- **Drift Detection**: Identifying when model performance degrades.

---

## 6. Common Pitfalls and Best Practices

- Always split data into train/validation/test sets.
- Don't forget to scale/normalize your features.
- Start with simple models before moving to complex ones.
- Monitor for data leakage between training and test sets.
- Document your experiments and hyperparameters.
- Consider computational resources and inference time.
- Be aware of bias in training data.

---

## End of Study Guide

"""

mock_markdown_kpop = """
# K-Pop Demon Hunters: A Comprehensive Study Guide

## 1. Introduction and Historical Context

### Origins of the K-Pop Demon Hunter Movement
The convergence of Korean pop music and supernatural defense began in Seoul during the late 1990s, coinciding with the rise of modern K-pop. As entertainment companies discovered that certain vocal frequencies and choreographic patterns could disrupt demonic energy fields, a secret society of performer-warriors emerged.

### Key Historical Events
- **1999 Seoul Incident**: First documented case of a K-pop group accidentally banishing a possession during a live performance
- **2005 Formation of SHIELD**: Secret Hunters International Entertainment & Logistics Division established
- **2012 Gangnam Exorcism**: Global recognition of K-pop's demon-fighting potential

## 2. Core Concepts and Terminology

### Essential Vocabulary

**Harmonic Banishment**: The practice of using specific vocal harmonies to create anti-demonic resonance fields that force supernatural entities back to their dimensional planes.

**Choreographic Sealing**: Dance movements that trace ancient protective sigils in three-dimensional space, creating barriers against demonic intrusion.

**Fan Chant Amplification**: The phenomenon where synchronized audience participation multiplies the demon-hunting effectiveness of a performance by creating a collective psychic shield.

**Lightstick Channeling**: The use of official group lightsticks as focusing tools for concentrated anti-demonic energy projection.

**Concept Transformation**: The ability of demon hunters to switch between cute, dark, and ethereal concepts to combat different demon classifications.

**Bias Wrecker Demon**: A particularly insidious type of demon that infiltrates fan communities by mimicking attractive idol characteristics.

### Classification of Demon Types

**Stage 1 - Sasaeng Spirits**: Low-level entities that feed on obsessive fan energy. Vulnerable to upbeat title tracks and synchronized dancing.

**Stage 2 - Anti-Demons**: Medium-threat demons that spread negativity through social media. Require coordinated sub-unit attacks and rap battles for elimination.

**Stage 3 - Black Ocean Entities**: Powerful demons that manifest during concerts as areas of darkness. Only defeatable through perfect vocal runs and high notes exceeding C6.

**Stage 4 - Disbandment Devils**: Ancient demons that target group cohesion. Demand full seven-member (or more) formations and emotional ballads for banishment.

## 3. Training and Skill Development

### Basic Training Requirements

All K-pop demon hunters must master:
- **Vocal Technique**: Minimum three-octave range with ability to maintain stability during acrobatic combat
- **Dance Precision**: Synchronization within 0.03 seconds of team members to maintain protective formations
- **Visual Power**: The ability to stun demons through perfectly timed eye contact with cameras
- **Language Multiplication**: Fluency in Korean, English, and at least one demonic dialect

### Advanced Techniques

**Aegyo Blast**: Weaponized cuteness that overloads demonic sensory systems, causing temporary paralysis.

**Rap God Summoning**: High-speed rap sequences that open portals to banish demons back to their origin dimensions.

**Vocal Run Barrier**: Extended melodic runs that create impenetrable sound walls lasting up to 30 seconds.

**Center Formation Strike**: When the center member channels the entire group's power into a single devastating attack.

## 4. Equipment and Tools

### Standard Demon Hunter Gear

**Performance Outfits**: Specially designed stage costumes embedded with blessed sequins and protective rhinestones. Each outfit is tailored to enhance specific combat abilities.

**In-Ear Monitors**: Modified communication devices that detect demonic presence within a 500-meter radius and provide real-time tactical updates.

**Microphones**: Enchanted with purification crystals, these serve as both performance tools and close-combat weapons against incorporeal entities.

**Platform Boots**: Provide elevation advantage and contain hidden compartments for holy water and sacred salts.

### Support Infrastructure

**Practice Rooms**: Reinforced facilities with spiritual barriers where demon hunters train 14-18 hours daily.

**Recording Studios**: Doubles as containment facilities for captured demons awaiting interrogation or banishment.

**Music Shows**: Weekly television programs that serve as public demonstration of demon-hunting capabilities while maintaining civilian cover.

## 5. Notable Demon Hunter Groups

### First Generation Legends
Established the foundational techniques still used today. Known for raw power over finesse.

### Second Generation Innovators
Introduced synchronized choreography seals and pioneered the use of social media for demon tracking.

### Third Generation Global Defenders
Expanded operations worldwide, establishing international demon response networks.

### Fourth Generation Tech Warriors
Integrate AR technology and AI-assisted demon prediction algorithms into traditional techniques.

## 6. Case Studies and Practical Applications

### The Midnight Seoul Operation
In 2018, a coordinated attack by Stage 3 demons during a major award show required three top groups to perform an emergency collaboration stage. The incident demonstrated the importance of inter-agency cooperation.

### The Viral Possession Incident
When a demon attempted to spread through a dance challenge video, quick-thinking idols created a counter-challenge that neutralized the threat within 48 hours.

## 7. Evaluation Metrics and Success Indicators

### Performance Metrics
- **Demon Banishment Rate (DBR)**: Successful eliminations per performance
- **Fan Shield Strength (FSS)**: Measured in collective decibels during fan chants
- **Choreographic Accuracy Index (CAI)**: Precision of protective movement patterns
- **Vocal Penetration Power (VPP)**: Ability to break through demonic defenses

### Key Performance Indicators
- Album sales directly correlate with regional demon suppression rates
- Music video views generate protective barriers around viewer devices
- Concert attendance creates temporary demon-free zones lasting 72 hours

## 8. Important Safety Protocols

**Never attempt demon hunting alone** - Always maintain minimum three-member formations for basic protection.

**Maintain regular comeback schedules** - Extended hiatuses weaken protective barriers and allow demon resurgence.

**Stay hydrated during battles** - Demon hunting while performing requires significant physical and spiritual energy.

**Monitor social media for possession signs** - Early detection prevents widespread demonic influence.

## End of Study Guide

Remember: The life of a K-pop demon hunter requires dedication, perfect pitch, and the ability to hit every beat while maintaining a flawless appearance. Fighting evil has never looked this good.
"""

def run_with_tavily(markdown_content):
    # Add tools to verification agent
    tools = create_tavily_tools()
    if tools:
        verification_agent.tools = tools
    # Attach tools to verification agent
    attach_tools_to_agent(verification_agent)
    
    # Create tasks and crew as normal
    crew = Crew(
        agents=[extraction_agent, verification_agent],
        tasks=[extraction_task, verification_task]
    )
    
    return crew.kickoff(inputs={"markdown": markdown_content})

def test_extraction_only(markdown: str):
    """Test just the extraction agent without verification"""
    print("\n" + "="*60)
    print("TEST 1: EXTRACTION ONLY")
    print("="*60)
    
    crew = Crew(
        agents=[extraction_agent],
        tasks=[extraction_task],
        verbose=True
    )
    
    result = crew.kickoff(inputs={"markdown": markdown})
    print("\nEXTRACTION RESULTS:")
    print("-"*40)
    print(result)
    return result

def test_with_verification_no_tavily(markdown: str):
    """Test extraction and verification without Tavily tools"""
    print("\n" + "="*60)
    print("TEST 2: EXTRACTION + VERIFICATION (No Tavily)")
    print("="*60)
    
    # Create verification task
    verification_task = Task(
        description=(
            "Review the extracted content and ensure accuracy.\n"
            "Organize and enhance the content based on your knowledge.\n"
            "Output clean, well-formatted markdown."
        ),
        expected_output="Verified markdown with vocabulary and key ideas",
        agent=verification_agent,
        context=[extraction_task]
    )
    
    crew = Crew(
        agents=[extraction_agent, verification_agent],
        tasks=[extraction_task, verification_task],
        verbose=True
    )
    
    result = crew.kickoff(inputs={"markdown": markdown})
    print("\nVERIFIED RESULTS (No Tavily):")
    print("-"*40)
    print(result)
    return result

def main():
    """Main test runner"""
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    print("TAV AGENT TEST SUITE")
    print("="*60)
    
    # Check for API keys
    print("\nEnvironment Check:")
    tavily_key = os.getenv('TAVILY_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    print(f"TAVILY_API_KEY: {'Found' if tavily_key else '❌ Not found'}")
    print(f"OPENAI_API_KEY: {'Found' if openai_key else '❌ Not found'}")
    
    if not openai_key:
        print("\nWarning: OPENAI_API_KEY not found")
        print("   CrewAI agents require OpenAI API key to function")
        print("   Please set OPENAI_API_KEY in your .env file")
        return
    
    # Run tests
    print("\n" + "testing...")
    
    # # Test 1: Extraction only
    # try:
    #     test_extraction_only(test_content)
    # except Exception as e:
    #     print(f"Extraction test failed: {e}")
    # 
    # # Test 2: Extraction + Verification (no Tavily)
    # try:
    #     test_with_verification_no_tavily(test_content)
    # except Exception as e:
    #     print(f"Verification test failed: {e}")
    
    # Test 2.5: W/tavily
    try:
        run_with_tavily(mock_markdown_kpop)
    except Exception as e:
        print(f"Verification test failed: {e}")
    
    # # Test 3: Full pipeline with Tavily (if API key available)
    # if tavily_key:
    #     try:
    #         test_with_tavily_verification(test_content)
    #     except Exception as e:
    #         print(f"Tavily verification test failed: {e}")
    # else:
    #     print("\n Skipping Tavily test (no API key)")
    
    print("\n" + "="*60)
    print("TEST SUITE COMPLETED")
    print("="*60)

if __name__ == "__main__":
    main()