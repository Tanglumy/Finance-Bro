"""
Formula Parser - Lexical analysis and parsing for formula DSL
"""

import re
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class TokenType(Enum):
    """Token types for the formula language."""
    # Literals
    NUMBER = "NUMBER"
    STRING = "STRING"
    IDENTIFIER = "IDENTIFIER"
    
    # Operators
    PLUS = "PLUS"
    MINUS = "MINUS"
    MULTIPLY = "MULTIPLY"
    DIVIDE = "DIVIDE"
    POWER = "POWER"
    MODULO = "MODULO"
    
    # Comparison
    EQUAL = "EQUAL"
    NOT_EQUAL = "NOT_EQUAL"
    LESS_THAN = "LESS_THAN"
    LESS_EQUAL = "LESS_EQUAL"
    GREATER_THAN = "GREATER_THAN"
    GREATER_EQUAL = "GREATER_EQUAL"
    
    # Logical
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    
    # Conditional
    QUESTION = "QUESTION"
    COLON = "COLON"
    
    # Delimiters
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LBRACKET = "LBRACKET"
    RBRACKET = "RBRACKET"
    COMMA = "COMMA"
    
    # Assignment
    ASSIGN = "ASSIGN"
    
    # End of formula
    EOF = "EOF"

@dataclass
class Token:
    """Represents a token in the formula."""
    type: TokenType
    value: Any
    position: int
    line: int = 1
    column: int = 1

@dataclass
class ASTNode:
    """Base class for AST nodes."""
    type: str
    value: Any = None
    children: List['ASTNode'] = None
    position: int = 0
    
    def __post_init__(self):
        if self.children is None:
            self.children = []

class FormulaLexer:
    """Lexical analyzer for formula expressions."""
    
    # Token patterns
    TOKEN_PATTERNS = [
        (r'#[^\n]*', None),  # Comments
        (r'\s+', None),      # Whitespace
        (r'\d+\.?\d*', TokenType.NUMBER),
        (r'"[^"]*"', TokenType.STRING),
        (r"'[^']*'", TokenType.STRING),
        (r'[a-zA-Z_][a-zA-Z0-9_]*', TokenType.IDENTIFIER),
        (r'\+', TokenType.PLUS),
        (r'-', TokenType.MINUS),
        (r'\*', TokenType.MULTIPLY),
        (r'/', TokenType.DIVIDE),
        (r'\^', TokenType.POWER),
        (r'%', TokenType.MODULO),
        (r'==', TokenType.EQUAL),
        (r'!=', TokenType.NOT_EQUAL),
        (r'<=', TokenType.LESS_EQUAL),
        (r'>=', TokenType.GREATER_EQUAL),
        (r'<', TokenType.LESS_THAN),
        (r'>', TokenType.GREATER_THAN),
        (r'&&', TokenType.AND),
        (r'\|\|', TokenType.OR),
        (r'!', TokenType.NOT),
        (r'\?', TokenType.QUESTION),
        (r':', TokenType.COLON),
        (r'\(', TokenType.LPAREN),
        (r'\)', TokenType.RPAREN),
        (r'\[', TokenType.LBRACKET),
        (r'\]', TokenType.RBRACKET),
        (r',', TokenType.COMMA),
        (r'=', TokenType.ASSIGN),
    ]
    
    def __init__(self):
        self.compiled_patterns = [(re.compile(pattern), token_type) 
                                 for pattern, token_type in self.TOKEN_PATTERNS]
    
    def tokenize(self, text: str) -> List[Token]:
        """Tokenize the input formula text."""
        tokens = []
        position = 0
        line = 1
        column = 1
        
        while position < len(text):
            match_found = False
            
            for pattern, token_type in self.compiled_patterns:
                match = pattern.match(text, position)
                if match:
                    value = match.group(0)
                    
                    # Skip whitespace and comments
                    if token_type is not None:
                        # Convert numeric values
                        if token_type == TokenType.NUMBER:
                            value = float(value) if '.' in value else int(value)
                        elif token_type == TokenType.STRING:
                            value = value[1:-1]  # Remove quotes
                        
                        tokens.append(Token(token_type, value, position, line, column))
                    
                    # Update position
                    position = match.end()
                    if '\n' in match.group(0):
                        line += match.group(0).count('\n')
                        column = len(match.group(0).split('\n')[-1])
                    else:
                        column += len(match.group(0))
                    
                    match_found = True
                    break
            
            if not match_found:
                raise SyntaxError(f"Unexpected character '{text[position]}' at line {line}, column {column}")
        
        tokens.append(Token(TokenType.EOF, None, position, line, column))
        return tokens

class FormulaParser:
    """Parser for formula expressions."""
    
    def __init__(self):
        self.lexer = FormulaLexer()
        self.tokens = []
        self.current = 0
        
    def parse(self, formula: str) -> ASTNode:
        """Parse a formula string into an AST."""
        try:
            self.tokens = self.lexer.tokenize(formula)
            self.current = 0
            
            # Parse assignment or expression
            if self._is_assignment():
                return self._parse_assignment()
            else:
                return self._parse_expression()
                
        except Exception as e:
            logger.error(f"Parse error in formula '{formula}': {e}")
            raise SyntaxError(f"Parse error: {e}")
    
    def _is_assignment(self) -> bool:
        """Check if the formula is an assignment."""
        # Look ahead for assignment operator
        for i in range(self.current, len(self.tokens)):
            if self.tokens[i].type == TokenType.ASSIGN:
                return True
            elif self.tokens[i].type in [TokenType.LPAREN, TokenType.QUESTION]:
                return False
        return False
    
    def _parse_assignment(self) -> ASTNode:
        """Parse assignment: variable = expression"""
        variable = self._consume(TokenType.IDENTIFIER, "Expected variable name")
        self._consume(TokenType.ASSIGN, "Expected '='")
        expression = self._parse_expression()
        
        return ASTNode(
            type="assignment",
            value=variable.value,
            children=[expression],
            position=variable.position
        )
    
    def _parse_expression(self) -> ASTNode:
        """Parse conditional expression: expr ? expr : expr"""
        expr = self._parse_logical_or()
        
        if self._match(TokenType.QUESTION):
            then_expr = self._parse_expression()
            self._consume(TokenType.COLON, "Expected ':' in conditional expression")
            else_expr = self._parse_expression()
            
            return ASTNode(
                type="conditional",
                children=[expr, then_expr, else_expr],
                position=expr.position
            )
        
        return expr
    
    def _parse_logical_or(self) -> ASTNode:
        """Parse logical OR expression."""
        expr = self._parse_logical_and()
        
        while self._match(TokenType.OR):
            operator = self._previous()
            right = self._parse_logical_and()
            expr = ASTNode(
                type="binary_op",
                value=operator.value,
                children=[expr, right],
                position=operator.position
            )
        
        return expr
    
    def _parse_logical_and(self) -> ASTNode:
        """Parse logical AND expression."""
        expr = self._parse_equality()
        
        while self._match(TokenType.AND):
            operator = self._previous()
            right = self._parse_equality()
            expr = ASTNode(
                type="binary_op",
                value=operator.value,
                children=[expr, right],
                position=operator.position
            )
        
        return expr
    
    def _parse_equality(self) -> ASTNode:
        """Parse equality expression."""
        expr = self._parse_comparison()
        
        while self._match(TokenType.EQUAL, TokenType.NOT_EQUAL):
            operator = self._previous()
            right = self._parse_comparison()
            expr = ASTNode(
                type="binary_op",
                value=operator.value,
                children=[expr, right],
                position=operator.position
            )
        
        return expr
    
    def _parse_comparison(self) -> ASTNode:
        """Parse comparison expression."""
        expr = self._parse_term()
        
        while self._match(TokenType.GREATER_THAN, TokenType.GREATER_EQUAL,
                         TokenType.LESS_THAN, TokenType.LESS_EQUAL):
            operator = self._previous()
            right = self._parse_term()
            expr = ASTNode(
                type="binary_op",
                value=operator.value,
                children=[expr, right],
                position=operator.position
            )
        
        return expr
    
    def _parse_term(self) -> ASTNode:
        """Parse addition and subtraction."""
        expr = self._parse_factor()
        
        while self._match(TokenType.PLUS, TokenType.MINUS):
            operator = self._previous()
            right = self._parse_factor()
            expr = ASTNode(
                type="binary_op",
                value=operator.value,
                children=[expr, right],
                position=operator.position
            )
        
        return expr
    
    def _parse_factor(self) -> ASTNode:
        """Parse multiplication, division, and modulo."""
        expr = self._parse_power()
        
        while self._match(TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.MODULO):
            operator = self._previous()
            right = self._parse_power()
            expr = ASTNode(
                type="binary_op",
                value=operator.value,
                children=[expr, right],
                position=operator.position
            )
        
        return expr
    
    def _parse_power(self) -> ASTNode:
        """Parse exponentiation."""
        expr = self._parse_unary()
        
        if self._match(TokenType.POWER):
            operator = self._previous()
            # Right associative
            right = self._parse_power()
            return ASTNode(
                type="binary_op",
                value=operator.value,
                children=[expr, right],
                position=operator.position
            )
        
        return expr
    
    def _parse_unary(self) -> ASTNode:
        """Parse unary expressions."""
        if self._match(TokenType.NOT, TokenType.MINUS):
            operator = self._previous()
            expr = self._parse_unary()
            return ASTNode(
                type="unary_op",
                value=operator.value,
                children=[expr],
                position=operator.position
            )
        
        return self._parse_call()
    
    def _parse_call(self) -> ASTNode:
        """Parse function calls and array access."""
        expr = self._parse_primary()
        
        while True:
            if self._match(TokenType.LPAREN):
                # Function call
                args = []
                if not self._check(TokenType.RPAREN):
                    args.append(self._parse_expression())
                    while self._match(TokenType.COMMA):
                        args.append(self._parse_expression())
                
                self._consume(TokenType.RPAREN, "Expected ')' after arguments")
                expr = ASTNode(
                    type="function_call",
                    value=expr.value if expr.type == "identifier" else None,
                    children=args,
                    position=expr.position
                )
            elif self._match(TokenType.LBRACKET):
                # Array access
                index = self._parse_expression()
                self._consume(TokenType.RBRACKET, "Expected ']' after array index")
                expr = ASTNode(
                    type="array_access",
                    children=[expr, index],
                    position=expr.position
                )
            else:
                break
        
        return expr
    
    def _parse_primary(self) -> ASTNode:
        """Parse primary expressions."""
        if self._match(TokenType.NUMBER):
            return ASTNode(
                type="number",
                value=self._previous().value,
                position=self._previous().position
            )
        
        if self._match(TokenType.STRING):
            return ASTNode(
                type="string",
                value=self._previous().value,
                position=self._previous().position
            )
        
        if self._match(TokenType.IDENTIFIER):
            return ASTNode(
                type="identifier",
                value=self._previous().value,
                position=self._previous().position
            )
        
        if self._match(TokenType.LPAREN):
            expr = self._parse_expression()
            self._consume(TokenType.RPAREN, "Expected ')' after expression")
            return expr
        
        current_token = self._peek()
        raise SyntaxError(f"Unexpected token '{current_token.value}' at position {current_token.position}")
    
    def _match(self, *types: TokenType) -> bool:
        """Check if current token matches any of the given types."""
        for token_type in types:
            if self._check(token_type):
                self._advance()
                return True
        return False
    
    def _check(self, token_type: TokenType) -> bool:
        """Check if current token is of given type."""
        if self._is_at_end():
            return False
        return self._peek().type == token_type
    
    def _advance(self) -> Token:
        """Consume and return current token."""
        if not self._is_at_end():
            self.current += 1
        return self._previous()
    
    def _is_at_end(self) -> bool:
        """Check if we're at the end of tokens."""
        return self._peek().type == TokenType.EOF
    
    def _peek(self) -> Token:
        """Return current token without consuming it."""
        return self.tokens[self.current]
    
    def _previous(self) -> Token:
        """Return previous token."""
        return self.tokens[self.current - 1]
    
    def _consume(self, token_type: TokenType, message: str) -> Token:
        """Consume token of expected type or raise error."""
        if self._check(token_type):
            return self._advance()
        
        current_token = self._peek()
        raise SyntaxError(f"{message}. Got '{current_token.value}' at position {current_token.position}")