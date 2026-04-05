# M-Pesa Testing Script (PowerShell)
# Run different M-Pesa tests from an interactive menu

function Show-Menu {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "                    M-PESA DARAJA API TESTING SUITE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Select a test option:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  1. Run Quick Manual Tests (Recommended for first run)" -ForegroundColor Green
    Write-Host "  2. Run All M-Pesa Tests (Django Test Suite)" -ForegroundColor Green
    Write-Host "  3. Run M-Pesa Service Tests Only" -ForegroundColor Green
    Write-Host "  4. Run M-Pesa API View Tests Only" -ForegroundColor Green
    Write-Host "  5. Run M-Pesa Integration Tests Only" -ForegroundColor Green
    Write-Host "  6. Run Specific Test" -ForegroundColor Green
    Write-Host "  7. View Testing Guide" -ForegroundColor Green
    Write-Host "  8. Exit" -ForegroundColor Green
    Write-Host ""
}

function Run-QuickTests {
    Write-Host ""
    Write-Host "Running Quick M-Pesa Tests..." -ForegroundColor Cyan
    Write-Host ""
    python quick_test_mpesa.py
    Write-Host ""
    Read-Host "Press Enter to continue"
}

function Run-AllTests {
    Write-Host ""
    Write-Host "Running All M-Pesa Tests..." -ForegroundColor Cyan
    Write-Host ""
    python manage.py test test_mpesa_comprehensive -v 2
    Write-Host ""
    Read-Host "Press Enter to continue"
}

function Run-ServiceTests {
    Write-Host ""
    Write-Host "Running M-Pesa Service Tests..." -ForegroundColor Cyan
    Write-Host ""
    python manage.py test test_mpesa_comprehensive.MpesaServiceTestCase -v 2
    Write-Host ""
    Read-Host "Press Enter to continue"
}

function Run-ViewTests {
    Write-Host ""
    Write-Host "Running M-Pesa API View Tests..." -ForegroundColor Cyan
    Write-Host ""
    python manage.py test test_mpesa_comprehensive.MpesaAPIViewsTestCase -v 2
    Write-Host ""
    Read-Host "Press Enter to continue"
}

function Run-IntegrationTests {
    Write-Host ""
    Write-Host "Running M-Pesa Integration Tests..." -ForegroundColor Cyan
    Write-Host ""
    python manage.py test test_mpesa_comprehensive.MpesaIntegrationTestCase -v 2
    Write-Host ""
    Read-Host "Press Enter to continue"
}

function Run-SpecificTest {
    Clear-Host
    Write-Host ""
    Write-Host "Available Specific Tests:" -ForegroundColor Yellow
    Write-Host ""
    
    $tests = @(
        "1. test_get_access_token",
        "2. test_stk_push_with_valid_phone",
        "3. test_stk_push_different_amounts",
        "4. test_stk_query",
        "5. test_account_balance",
        "6. test_b2c_payment",
        "7. test_b2b_payment",
        "8. test_transaction_status",
        "9. test_dynamic_qr_code",
        "10. test_reversal",
        "11. test_phone_number_formatting",
        "12. test_phone_number_validation",
        "13. test_complete_payment_flow"
    )
    
    foreach ($test in $tests) {
        Write-Host "  $test" -ForegroundColor Green
    }
    
    Write-Host ""
    $testChoice = Read-Host "Enter test number or full test name"
    
    $testMap = @{
        "1" = "test_get_access_token"
        "2" = "test_stk_push_with_valid_phone"
        "3" = "test_stk_push_different_amounts"
        "4" = "test_stk_query"
        "5" = "test_account_balance"
        "6" = "test_b2c_payment"
        "7" = "test_b2b_payment"
        "8" = "test_transaction_status"
        "9" = "test_dynamic_qr_code"
        "10" = "test_reversal"
        "11" = "test_phone_number_formatting"
        "12" = "test_phone_number_validation"
        "13" = "test_complete_payment_flow"
    }
    
    if ($testMap.ContainsKey($testChoice)) {
        $testName = $testMap[$testChoice]
    } else {
        $testName = $testChoice
    }
    
    Clear-Host
    Write-Host ""
    Write-Host "Running Test: $testName" -ForegroundColor Cyan
    Write-Host ""
    python manage.py test test_mpesa_comprehensive.MpesaServiceTestCase.$testName -v 2
    Write-Host ""
    Read-Host "Press Enter to continue"
}

function View-Guide {
    Clear-Host
    Write-Host ""
    Write-Host "Opening M-Pesa Testing Guide..." -ForegroundColor Cyan
    Write-Host ""
    
    if (Test-Path "MPESA_TESTING_GUIDE.md") {
        Get-Content MPESA_TESTING_GUIDE.md | more
    } else {
        Write-Host "Testing guide not found." -ForegroundColor Red
    }
    
    Write-Host ""
    Read-Host "Press Enter to continue"
}

# Main loop
while ($true) {
    Clear-Host
    Show-Menu
    
    $choice = Read-Host "Enter your choice (1-8)"
    
    switch ($choice) {
        "1" { Run-QuickTests }
        "2" { Run-AllTests }
        "3" { Run-ServiceTests }
        "4" { Run-ViewTests }
        "5" { Run-IntegrationTests }
        "6" { Run-SpecificTest }
        "7" { View-Guide }
        "8" {
            Write-Host ""
            Write-Host "Goodbye!" -ForegroundColor Yellow
            Write-Host ""
            exit
        }
        default {
            Write-Host "Invalid choice. Please try again." -ForegroundColor Red
            Start-Sleep -Seconds 2
        }
    }
}