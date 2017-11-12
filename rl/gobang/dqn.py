# -*- coding: utf-8 -*-
import random
import gym
import gym_gomoku
import numpy as np
from collections import deque
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Conv2D
from keras.layers import MaxPooling2D
from keras.layers import Flatten
from keras.layers import Dropout
from keras.optimizers import Adam

from keras import backend as K
K.set_image_dim_ordering('tf')

EPISODES = 50000

class DQNAgent:
    def __init__(self, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=2000)
        self.gamma = 0.95    # discount rate
        self.epsilon = 1.0  # exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.999
        self.learning_rate = 0.001
        self.model = self._build_model()

    def _build_model(self):
        # Neural Net for Deep-Q learning Model
        model = Sequential()
        model.add(Conv2D(16, kernel_size=(5, 5), strides=(1, 1),
                         activation='relu',
                         padding='same',
                         input_shape=(9,9,1)))
        model.add(MaxPooling2D(pool_size=(2, 2), padding='same', strides=(2, 2)))
        model.add(Conv2D(32, (5, 5), activation='relu', padding='same'))
        model.add(MaxPooling2D(pool_size=(2, 2), padding='same', strides=(2, 2)))
        model.add(Dropout(0.25))
        model.add(Flatten())
        model.add(Dense(128, activation='relu'))
        model.add(Dense(self.action_size, activation='linear'))
        model.compile(loss='mse',
                      optimizer=Adam(lr=self.learning_rate))
        return model

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state):
        if np.random.rand() <= self.epsilon:
            act = random.randrange(self.action_size)
        else:
            state = np.reshape(state, [1, 9, 9, 1])
            act_values = self.model.predict(state)
            act = np.argmax(act_values[0])  # returns action

        map = np.reshape(state, (action_size))
        while (map[act] > 0):
            act = random.randrange(self.action_size)
        return act

    def replay(self, batch_size):
        minibatch = random.sample(self.memory, batch_size)
        for state, action, reward, next_state, done in minibatch:
            target = reward
            if not done:
                target = (reward + self.gamma *
                          np.amax(self.model.predict(next_state)[0]))
            state = np.reshape(state, [1, 9, 9, 1])
            target_f = self.model.predict(state)
            target_f[0][action] = target
            self.model.fit(state, target_f, epochs=1, verbose=0)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def load(self, name):
        self.model.load_weights(name)

    def save(self, name):
        self.model.save_weights(name)

if __name__ == "__main__":
    env = gym.make('Gomoku9x9-v0')
    state_size = env.observation_space.shape
    action_size = env.action_space.n
    print('state_size: ' + str(state_size))
    print('action_size: ' + str(action_size))
    agent = DQNAgent(state_size, action_size)

    max_steps = 100
    done = False
    batch_size = 32

    for e in range(EPISODES):
        state = env.reset()
        total_reward = 0.0
        #env.render()

        for i in range(max_steps):
            #print(state)
            action = agent.act(state)
            #print("action: " + str(action))
            #print("stone: " + str(np.reshape(state, (action_size))[action]))
            next_state, reward, done, _ = env.step(action)
            reward = reward if done else 0.01
            total_reward += reward
            if (e%100 == 0):
                env.render()
            next_state = np.reshape(next_state, [1, 9, 9, 1])
            agent.remember(state, action, reward, next_state, done)
            state = next_state
            if done:
                print("episode: {}/{}, step: {}, e: {:.2}, r: {}, total_reward: {:.2}"
                      .format(e, EPISODES, i, agent.epsilon, reward, total_reward))
                break
            if len(agent.memory) > batch_size:
                agent.replay(batch_size)