function norm(v)
    return sqrt(v[1]^2 + v[2]^2 + v[3]^2)
end

function run()
    body1_pos = [0.0, 1.0, 0.0]
    body1_vel = [5.775e-6, 0.0, 0.0]
    body1_mass = 2.0
    
    body2_pos = [0.0, -1.0, 0.0]
    body2_vel = [-5.775e-6, 0.0, 0.0]
    body2_mass = 2.0
    
    G = 6.673e-11
    
    time_step = 0.1
    
    for step in 1:10000
        r = body2_pos - body1_pos
        r_norm = norm(r)
        r_hat = r / r_norm
        F = G * body1_mass * body2_mass / r_norm^2 * r_hat
        body1_acc = F / body1_mass
        body2_acc = -F / body2_mass
        body1_vel += body1_acc * time_step
        body2_vel += body2_acc * time_step
        body1_pos += body1_vel * time_step
        body2_pos += body2_vel * time_step
        if step % 1000 == 0
            println("Step: ", step)
            println("Body 1 position: ", body1_pos)
            println("Body 2 position: ", body2_pos)
        end
    end
end

run()
