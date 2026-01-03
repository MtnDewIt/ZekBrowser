export class ValidationError extends Error 
{
    constructor(message: string, errors: string[]) 
    {
        super(message);
        this.errors = errors;
    }
}
