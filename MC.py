import numpy as np

from utils import onehot, decide, importance_sampling_ratio, mse

class MC_LEARNER():
    def __init__(self, env):
        self.observation_space, self.action_space = env.observation_space, env.action_space

        self.return_counts = np.zeros(self.observation_space.n)
        self.return_sums = np.zeros(self.observation_space.n)
        self.return_square_sums = np.zeros(self.observation_space.n)

        self.expected_return = np.zeros(self.observation_space.n)
        self.variance_of_return = np.zeros(self.observation_space.n)

    def backward_step(self, state, G):
        self.return_sums[state] += G
        self.return_counts[state] += 1

        old_expectation = self.expected_return[state]
        new_expectation = self.return_sums[state] / self.return_counts[state]
        self.return_square_sums[state] += (G - old_expectation) * (G - new_expectation)

        self.expected_return[state] = new_expectation
        self.variance_of_return[state] = self.return_square_sums[state] / self.return_counts[state]


def MC(env, episodes, target, behavior, Lambda, gamma = lambda x: 0.95, alpha = 0.05, beta = 0.0001, diagnose = False):
    """
    episodes:   number of episodes
    target:     target policy matrix (|S|*|A|)
    behavior:   behavior policy matrix (|S|*|A|)
    Lambda:     LAMBDA object determining each lambda for each feature (or state or observation)
    gamma:      anonymous function determining each lambda for each feature (or state or observation)
    alpha:      learning rate for the weight vector of the values
    beta:       learning rate for the auxiliary vector for off-policy
    """
    learner = MC_LEARNER(env)
    expected_return_trace = []
    variance_of_return_trace = []

    for _ in range(episodes):
        state, done = env.reset(), False

        # Get the (s, a, r) pairs for an entire episode.
        episode = []
        done = False
        while not done:
            action = decide(state, behavior)
            next_state, reward, done, _ = env.step(action)
            if done:
                learner.return_counts[next_state] += 1
            episode.append((state, action, reward))
            state = next_state

        expected_return_trace.append(np.copy(learner.expected_return))
        variance_of_return_trace.append(np.copy(learner.variance_of_return))

        # Update expected G for every visit.
        G = 0.0
        for t in range(len(episode)-1, -1, -1):
            gamma_val = gamma(state)
            state, action, reward = episode[t]
            rho = importance_sampling_ratio(target, behavior, state, action)
            G = rho*(reward + gamma_val * G)

            learner.backward_step(state, G)

    return expected_return_trace, variance_of_return_trace, learner.return_counts