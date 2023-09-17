use std::{
    io::{self, Write},
    rc::Rc,
};

use abilene::{exc, run};

const PREAMBLE: &str = "@help @@I\\\\\\ hope\\\\\\ you\\\\\\ are\\\\\\ enjoying\\\\\\ abilene\\\\\\ syntax!\\\\\\ Here\\\\\\ is\\\\\\ an\\\\\\ example\\\\\\ for\\\\\\ you\\\\\\ to\\\\\\ help:\\\\nFactorial\\\\\\ calculation:\\\\\\ @fact\\\\\\ @@arg\\\\\\\\\\\\\\ ^\\\\\\\\\\\\\\ '0\\\\\\\\\\\\\\ =\\\\\\\\\\\\\\ ~\\\\\\\\\\\\\\ '1\\\\\\\\\\\\\\ @arg\\\\\\\\\\\\\\ ^\\\\\\\\\\\\\\ @arg\\\\\\\\\\\\\\ ^\\\\\\\\\\\\\\ '1\\\\\\\\\\\\\\ -\\\\\\\\\\\\\\ @arg\\\\\\\\\\\\\\ $$\\\\\\\\\\\\\\ :fact\\\\\\\\\\\\\\ ,\\\\\\\\\\\\\\ *\\\\\\\\\\\\\\ {\\\\\\ $\\\\nCall\\\\\\ it:\\\\\\ '4\\\\\\ @arg\\\\\\ $$\\\\\\ :fact\\\\\\ ,\\\\\\ `\\ ` $";

fn main() {
    let mut ctx = exc::create_context();

    if let Err(err) = run(&mut ctx, Rc::new(String::from(PREAMBLE))) {
        println!("Error: {}\n{}", err.error, err.apply());
    }

    println!("Welcome to abilene repl!");
    println!("Type ':help' to view help or 'quit' to quit repl");

    loop {
        print!("> ");
        io::stdout().flush().unwrap();
        let mut code = String::new();
        io::stdin().read_line(&mut code).unwrap();
        code = code.trim().to_owned();

        if code == "quit" {
            break;
        }

        if let Err(err) = run(&mut ctx, Rc::new(code)) {
            println!("Error: {}\n{}", err.error, err.apply());
        }
    }
}
