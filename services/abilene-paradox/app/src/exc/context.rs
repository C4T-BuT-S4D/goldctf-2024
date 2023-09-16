use std::{collections::HashMap, io::Write, rc::Rc};

use crate::{
    ast::{
        node::{Atom, Node},
        value::Value,
    },
    error::LanguageError,
    lex, prs,
};

#[derive(Default)]
pub struct Context {
    variables: HashMap<String, Value>,
}

impl Context {
    pub fn exec(&mut self, ast: Atom) -> Result<Value, LanguageError> {
        let span = ast.span.clone();
        match ast.node {
            Node::Const(v) => Ok(v),

            Node::Add(l, r) => {
                let l = self.exec(*l)?;
                let r = self.exec(*r)?;
                match l {
                    Value::I(l) => {
                        if let Value::I(r) = r {
                            Ok(Value::I(l + r))
                        } else {
                            Err(LanguageError {
                                code: ast.code,
                                error: "can't add string to int".to_owned(),
                                span,
                            })
                        }
                    }
                    Value::S(l) => {
                        if let Value::S(r) = r {
                            Ok(Value::S(l + &r))
                        } else {
                            Err(LanguageError {
                                code: ast.code,
                                error: "can't add int to string".to_owned(),
                                span,
                            })
                        }
                    }
                }
            }

            Node::Sub(l, r) => {
                let l = self.exec(*l)?;
                let r = self.exec(*r)?;
                match l {
                    Value::I(l) => {
                        if let Value::I(r) = r {
                            Ok(Value::I(l - r))
                        } else {
                            Err(LanguageError {
                                code: ast.code,
                                error: "can't sub string from int".to_owned(),
                                span,
                            })
                        }
                    }
                    Value::S(_) => Err(LanguageError {
                        code: ast.code,
                        error: "can't sub from string".to_owned(),
                        span,
                    }),
                }
            }

            Node::Mul(l, r) => {
                let l = self.exec(*l)?;
                let r = self.exec(*r)?;
                match l {
                    Value::I(l) => {
                        if let Value::I(r) = r {
                            Ok(Value::I(l * r))
                        } else {
                            Err(LanguageError {
                                code: ast.code,
                                error: "can't mul int by string".to_owned(),
                                span,
                            })
                        }
                    }
                    Value::S(_) => Err(LanguageError {
                        code: ast.code,
                        error: "can't mul string".to_owned(),
                        span,
                    }),
                }
            }

            Node::Div(l, r) => {
                let l = self.exec(*l)?;
                let r = self.exec(*r)?;
                match l {
                    Value::I(l) => {
                        if let Value::I(r) = r {
                            Ok(Value::I(l / r))
                        } else {
                            Err(LanguageError {
                                code: ast.code,
                                error: "can't div int by string".to_owned(),
                                span,
                            })
                        }
                    }
                    Value::S(_) => Err(LanguageError {
                        code: ast.code,
                        error: "can't div string".to_owned(),
                        span,
                    }),
                }
            }

            Node::Exec(v) => {
                let v = self.exec(*v)?;
                match v {
                    Value::I(_) => Err(LanguageError {
                        code: ast.code,
                        error: "can't exec int".to_owned(),
                        span,
                    }),
                    Value::S(v) => self.exec(lex::build_ast(prs::parse(Rc::new(v)))?),
                }
            }

            Node::Second(l, r) => {
                self.exec(*l)?;
                self.exec(*r)
            }

            Node::Show(v) => {
                let v = self.exec(*v)?;
                let s = match v {
                    Value::I(v) => format!("{v}"),
                    Value::S(v) => format!("{v}"),
                };
                print!("{s}");
                Ok(Value::I(s.chars().count() as i64))
            }

            Node::ShowLn(v) => {
                let v = self.exec(*v)?;
                let s = match v {
                    Value::I(v) => format!("{v}"),
                    Value::S(v) => format!("{v}"),
                };
                println!("{s}");
                Ok(Value::I(s.chars().count() as i64))
            }

            Node::Write(l, r) => {
                let l = self.exec(*l)?;
                let r = self.exec(*r)?;
                match l {
                    Value::I(_) => Err(LanguageError {
                        code: ast.code,
                        error: "can't use int as file name".to_owned(),
                        span,
                    }),
                    Value::S(l) => match r {
                        Value::I(_) => Err(LanguageError {
                            code: ast.code,
                            error: "can't write int to file".to_owned(),
                            span,
                        }),
                        Value::S(r) => {
                            let Ok(mut f) = std::fs::File::create_new(l) else {
                                return Err(LanguageError {
                                    code: ast.code,
                                    error: "can't create new file".to_owned(),
                                    span,
                                })
                            };
                            if f.write_all(r.as_bytes()).is_err() {
                                Err(LanguageError {
                                    code: ast.code,
                                    error: "can't write to file".to_owned(),
                                    span,
                                })
                            } else {
                                Ok(Value::I(r.chars().count() as i64))
                            }
                        }
                    },
                }
            }

            Node::Append(l, r) => {
                let l = self.exec(*l)?;
                let r = self.exec(*r)?;
                match l {
                    Value::I(_) => Err(LanguageError {
                        code: ast.code,
                        error: "can't use int as file name".to_owned(),
                        span,
                    }),
                    Value::S(l) => match r {
                        Value::I(_) => Err(LanguageError {
                            code: ast.code,
                            error: "can't write int to file".to_owned(),
                            span,
                        }),
                        Value::S(r) => {
                            let Ok(mut f) = std::fs::OpenOptions::new().append(true).open(l) else {
                                return Err(LanguageError {
                                    code: ast.code,
                                    error: "can't create new file".to_owned(),
                                    span,
                                })
                            };
                            if f.write_all(r.as_bytes()).is_err() {
                                Err(LanguageError {
                                    code: ast.code,
                                    error: "can't write to file".to_owned(),
                                    span,
                                })
                            } else {
                                Ok(Value::I(r.chars().count() as i64))
                            }
                        }
                    },
                }
            }

            Node::Read(v) => {
                let v = self.exec(*v)?;
                match v {
                    Value::I(_) => Err(LanguageError {
                        code: ast.code,
                        error: "can't use int as file name".to_owned(),
                        span,
                    }),
                    Value::S(v) => {
                        let Ok(s) = std::fs::read_to_string(v) else {
                            return Err(LanguageError {
                                code: ast.code,
                                error: "can't read from file".to_owned(),
                                span,
                            })
                        };

                        Ok(Value::S(s))
                    }
                }
            }

            Node::Define(l, r) => {
                let l = self.exec(*l)?;
                let r = self.exec(*r)?;
                match l {
                    Value::I(_) => Err(LanguageError {
                        code: ast.code,
                        error: "can't use int as variable name".to_owned(),
                        span,
                    }),
                    Value::S(l) => {
                        self.variables.insert(l, r.clone());
                        Ok(r)
                    }
                }
            }

            Node::Access(v) => {
                let v = self.exec(*v)?;
                match v {
                    Value::I(_) => Err(LanguageError {
                        code: ast.code,
                        error: "can't access int".to_owned(),
                        span,
                    }),
                    Value::S(v) => self
                        .variables
                        .get(&v)
                        .ok_or(LanguageError {
                            code: ast.code,
                            error: "no such variable".to_owned(),
                            span,
                        })
                        .map(Clone::clone),
                }
            }

            Node::Call(v) => {
                let v = self.exec(*v)?;
                match v {
                    Value::I(_) => Err(LanguageError {
                        code: ast.code,
                        error: "can't call int".to_owned(),
                        span,
                    }),
                    Value::S(v) => {
                        let v = self.variables.get(&v).ok_or(LanguageError {
                            code: ast.code.clone(),
                            error: "no such variable".to_owned(),
                            span: span.clone(),
                        })?;
                        match v {
                            Value::I(_) => Err(LanguageError {
                                code: ast.code.clone(),
                                error: "can't exec int".to_owned(),
                                span,
                            }),
                            Value::S(v) => self.exec(lex::build_ast(prs::parse(Rc::new(v.to_string())))?),
                        }
                    }
                }
            }

            Node::InlineCall(v) => {
                let v = self.variables.get(&v).ok_or(LanguageError {
                    code: ast.code.clone(),
                    error: "no such variable".to_owned(),
                    span: span.clone(),
                })?;
                match v {
                    Value::I(_) => Err(LanguageError {
                        code: ast.code,
                        error: "can't exec int".to_owned(),
                        span,
                    }),
                    Value::S(v) => self.exec(lex::build_ast(prs::parse(Rc::new(v.to_string())))?),
                }
            }

            Node::Eq(l, r) => {
                let l = self.exec(*l)?;
                let r = self.exec(*r)?;
                match l {
                    Value::I(l) => {
                        if let Value::I(r) = r {
                            Ok(Value::I(i64::from(l == r)))
                        } else {
                            Err(LanguageError {
                                code: ast.code,
                                error: "can't compare string to int".to_owned(),
                                span,
                            })
                        }
                    }
                    Value::S(l) => {
                        if let Value::S(r) = r {
                            Ok(Value::I(i64::from(l == r)))
                        } else {
                            Err(LanguageError {
                                code: ast.code,
                                error: "can't compare int to string".to_owned(),
                                span,
                            })
                        }
                    }
                }
            }

            Node::Lt(l, r) => {
                let l = self.exec(*l)?;
                let r = self.exec(*r)?;
                match l {
                    Value::I(l) => {
                        if let Value::I(r) = r {
                            Ok(Value::I(i64::from(l < r)))
                        } else {
                            Err(LanguageError {
                                code: ast.code,
                                error: "can't compare string to int".to_owned(),
                                span,
                            })
                        }
                    }
                    Value::S(l) => {
                        if let Value::S(r) = r {
                            Ok(Value::I(i64::from(l < r)))
                        } else {
                            Err(LanguageError {
                                code: ast.code,
                                error: "can't compare int to string".to_owned(),
                                span,
                            })
                        }
                    }
                }
            }

            Node::Not(v) => {
                let v = self.exec(*v)?;
                match v {
                    Value::I(v) => Ok(Value::I(i64::from(v == 0))),
                    Value::S(_) => Err(LanguageError {
                        code: ast.code,
                        error: "can't not string".to_owned(),
                        span,
                    }),
                }
            }

            Node::And(l, r) => {
                let l = self.exec(*l)?;
                let r = self.exec(*r)?;
                match l {
                    Value::I(l) => {
                        if let Value::I(r) = r {
                            Ok(Value::I(i64::from(l != 0 && r != 0)))
                        } else {
                            Err(LanguageError {
                                code: ast.code,
                                error: "can't and int and string".to_owned(),
                                span,
                            })
                        }
                    }
                    Value::S(_) => Err(LanguageError {
                        code: ast.code,
                        error: "can't and string".to_owned(),
                        span,
                    }),
                }
            }
        }
    }
}
