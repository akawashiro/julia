# Function to calculate the sum of numbers from 1 to 1000
function sum_1_to_n(n)
    return sum(1:n)
end

# Calling the function and printing the result
result = sum_1_to_n(1000)
println("The sum of numbers from 1 to 1000 is: $result")

show(code_typed(sum_1_to_n))
println("\n")
