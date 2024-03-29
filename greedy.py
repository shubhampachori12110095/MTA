import gym, numpy as np
from utils import *
from methods import *
from true_online_GTD import *

def eval_greedy_per_run(env, runtime, runtimes, episodes, target, behavior, gamma, Lambda, alpha, beta, evaluation):
    print('running %d of %d for greedy' % (runtime + 1, runtimes))
    value_trace, lambda_trace, var_trace = greedy(env, episodes, target, behavior, Lambda, gamma = lambda x: 0.95, alpha = 0.05, beta = 0.0001, diagnose = False, evaluation = evaluation)
    return (value_trace, lambda_trace, var_trace)

def eval_greedy(env, expectation, variance, stat_dist, behavior, target, gamma = lambda x: 0.95, alpha=0.05, beta=0.05, runtimes=20, episodes=int(1e5), evaluation = None):
    LAMBDAS = []
    for runtime in range(runtimes):
        LAMBDAS.append(LAMBDA(env, lambda_type = 'constant', initial_value = np.ones(env.observation_space.n)))
    results = Parallel(n_jobs = -1)(delayed(eval_greedy_per_run)(env, runtime, runtimes, episodes, target, behavior, gamma, LAMBDAS[runtime], alpha, beta, evaluation) for runtime in range(runtimes))
    value_traces = [entry[0] for entry in results]
    lambda_trace = [entry[1] for entry in results]
    var_traces = [entry[2] for entry in results]
    if evaluation is None:
        error_value = np.zeros((runtimes, episodes))
        error_var = np.zeros((runtimes, episodes))
        for runtime in range(runtimes):
            w_trace = var_traces[runtime]
            for j in range(len(w_trace)):
                error_var[runtime, j] = mse(w_trace[j], variance, stat_dist)
        for runtime in range(runtimes):
            w_trace = value_traces[runtime]
            for j in range(len(w_trace)):
                error_value[runtime, j] = mse(w_trace[j], expectation, stat_dist)
        return error_value, np.concatenate(lambda_trace, axis = 1).T, error_var
    else:
        return np.concatenate(value_traces, axis = 1).T, np.concatenate(lambda_trace, axis = 1).T, np.concatenate(var_traces, axis = 1).T

def greedy(env, episodes, target, behavior, Lambda, gamma = lambda x: 0.95, alpha = 0.05, beta = 0.05, diagnose = False, evaluation = None):
    N = env.observation_space.n
    lambda_trace = np.zeros((episodes, 1))
    lambda_trace[:] = np.nan
    first_moment_learner, variance_learner, value_learner = TRUE_ONLINE_GTD_LEARNER(env), TRUE_ONLINE_GTD_LEARNER(env), TRUE_ONLINE_GTD_LEARNER(env)
    variance_learner.w_prev, variance_learner.w_curr = np.zeros(env.observation_space.n), np.zeros(env.observation_space.n)
    if evaluation is not None:
        value_trace, var_trace = np.zeros((episodes, 1)), np.zeros((episodes, 1))
        value_trace[:] = np.nan; var_trace[:] = np.nan
    else:
        value_trace, var_trace = [], []
    for epi in range(episodes):
        s_curr, done = env.reset(), False
        starting_state = s_curr
        x_curr = onehot(s_curr, N)
        value_learner.refresh(); first_moment_learner.refresh(); variance_learner.refresh()
        if evaluation is not None:
            value_trace[epi, 0] = evaluation(value_learner.w_curr, 'expectation')
            var_trace[epi, 0] = evaluation(variance_learner.w_curr, 'variance')
        else:
            value_trace.append(np.copy(value_learner.w_curr))
            var_trace.append(np.copy(variance_learner.w_curr))
        while not done:
            action = decide(s_curr, behavior)
            rho_curr = importance_sampling_ratio(target, behavior, s_curr, action)
            s_next, R_next, done, _ = env.step(action)
            x_next = onehot(s_next, N)
            first_moment_learner.learn(R_next, gamma(x_next), gamma(x_curr), x_next, x_curr, 1.0, 1.0, rho_curr, alpha, beta)
            delta_curr = R_next + gamma(x_next) * np.dot(x_next, value_learner.w_curr) - np.dot(x_curr, value_learner.w_curr)
            r_bar_next = delta_curr ** 2
            gamma_bar_next = (rho_curr * gamma(x_next)) ** 2
            variance_learner.learn(r_bar_next, gamma_bar_next, 1, x_next, x_curr, 1, 1, 1, alpha, beta)
            errsq = (np.dot(x_next, first_moment_learner.w_next) - np.dot(x_next, value_learner.w_curr)) ** 2
            varg = max(0, np.dot(x_next, variance_learner.w_next))
            if errsq + varg > 0:
                Lambda.w[s_next] = errsq / (errsq + varg)
            if s_curr == starting_state and s_next == starting_state + 1:
                lambda_trace[epi, 0] = Lambda.w[s_next]
                if diagnose:
                    print("s_curr %d s_next %d errsq %.2e, varg %.2e, lambda_next %.2e" % (s_curr, s_next, errsq, varg, Lambda.w[s_next]))
            value_learner.learn(R_next, gamma(x_next), gamma(x_curr), x_next, x_curr, Lambda.value(x_next), Lambda.value(x_curr), rho_curr, alpha, beta)
            first_moment_learner.next(); variance_learner.next(); value_learner.next()
            s_curr, x_curr = s_next, x_next
    return value_trace, lambda_trace, var_trace