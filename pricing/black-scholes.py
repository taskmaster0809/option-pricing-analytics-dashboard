from scipy.stats import norm
import numpy as np


class EuropeanOption:
    def __init__(self, S, K, T, r, sigma):
        if S <= 0 or K <= 0 or T <= 0 or sigma <= 0:
            raise ValueError("S, K, T and sigma must be strictly positive")

        self.S = S
        self.K = K
        self.T = T
        self.r = r
        self.sigma = sigma

    def _d1_d2(self):
        d1 = (np.log(self.S / self.K) + (self.r + self.sigma ** 2 / 2) * self.T) / (self.sigma * np.sqrt(self.T))
        d2 = d1 - self.sigma * np.sqrt(self.T)
        return d1, d2

    def call_price(self): # Under Black Scholes Model
        d1, d2 = self._d1_d2()
        return self.S * norm.cdf(d1) - norm.cdf(d2) * self.K * np.exp(-self.r * self.T)

    def put_price(self): # Under Black Scholes Model
        d1, d2 = self._d1_d2()
        return -self.S * norm.cdf(-d1) + norm.cdf(-d2) * self.K * np.exp(-self.r * self.T)

    def greeks(self):
        d1, d2 = self._d1_d2()
        delta_call = norm.cdf(d1)
        delta_put = delta_call - 1
        gamma = norm.pdf(d1)/(self.S * self.sigma * np.sqrt(self.T))
        vega = self.S * norm.pdf(d1) * np.sqrt(self.T)
        rho_call = self.K * self.T * np.exp(-self.r * self.T) * norm.cdf(d2)
        rho_put = -self.K * self.T * np.exp(-self.r * self.T) * norm.cdf(-d2)

        theta_call = (-self.S * norm.pdf(d1) * self.sigma/(2 * np.sqrt(self.T)) -
                      self.r * self.K * norm.cdf(d2) * np.exp(-self.r * self.T))

        theta_put = (-self.S * norm.pdf(d1) * self.sigma/(2 * np.sqrt(self.T)) +
                      self.r * self.K * norm.cdf(-d2) * np.exp(-self.r * self.T))

        result_dict = {
            "call": {
                "delta": delta_call,
                "gamma": gamma,
                "vega": vega,
                "rho": rho_call,
                "theta": theta_call,
            },
            "put": {
                "delta": delta_put,
                "gamma": gamma,
                "vega": vega,
                "rho": rho_put,
                "theta": theta_put,
            }
        }
        return result_dict

    def monte_carlo_price(self, N): # Under Geometric Brownian Motion assumption
        # Random Normal Variates
        rng = np.random.default_rng()
        pos_z = rng.normal(0, 1, N)
        neg_z = -pos_z # Antithetic

        # Simulating stock price under risk neutral measure
        pos_s_t = self.S * np.exp((self.r - self.sigma**2/2) * self.T + self.sigma * np.sqrt(self.T) * pos_z)
        neg_s_t = self.S * np.exp((self.r - self.sigma**2/2) * self.T + self.sigma * np.sqrt(self.T) * neg_z)

        # Using antithetic variates variance reduction technique
        call_price = (np.exp(-self.r * self.T) *
                      np.mean((np.maximum(pos_s_t - self.K, 0) + np.maximum(neg_s_t - self.K, 0))/2))

        put_price = (np.exp(-self.r * self.T) *
                     np.mean((np.maximum(self.K - pos_s_t, 0) + np.maximum(self.K - neg_s_t, 0))/2))
        return call_price, put_price

