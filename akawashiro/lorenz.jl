using DifferentialEquations

function lorenz(u, p, t)
    dx = 10.0 * (u[2] - u[1])
    dy = u[1] * (28.0 - u[3]) - u[2]
    dz = u[1] * u[2] - (8 / 3) * u[3]
    [dx, dy, dz]
end

u0 = [1.0; 0.0; 0.0]
tspan = (0.0, 1000.0)
prob = ODEProblem(lorenz, u0, tspan)
solve(prob, Tsit5());
